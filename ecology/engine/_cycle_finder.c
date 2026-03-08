/*
 * ESDE Genesis — Accelerated Cycle Finder
 * =========================================
 * C extension replacing GenesisState.find_all_cycles()
 * Algorithm: identical to Python version (DFS with canonical dedup)
 * Output: identical (same canonical forms, same cycle counts)
 *
 * Build: python build_cycle_finder.py
 * Test:  python test_cycle_finder.py
 */

#include <Python.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAX_CYC 8   /* max cycle elements (max_length + 1 for closing node) */

/* ================================================================
 * Canonical cycle form (matches Python _canonical_cycle exactly)
 * ================================================================ */
static void cycle_canonicalize(const int *cycle, int len, int *out) {
    int i, min_pos = 0;
    int rot[MAX_CYC] = {0}, rev[MAX_CYC] = {0};

    /* Find first occurrence of min element */
    for (i = 1; i < len; i++)
        if (cycle[i] < cycle[min_pos]) min_pos = i;

    /* Rotate min to front */
    for (i = 0; i < len; i++)
        rot[i] = cycle[(min_pos + i) % len];

    /* Reverse (keep first, reverse rest) */
    rev[0] = rot[0];
    for (i = 1; i < len; i++)
        rev[i] = rot[len - i];

    /* Take lexicographically smaller */
    int use_rev = 0;
    for (i = 1; i < len; i++) {
        if (rev[i] < rot[i]) { use_rev = 1; break; }
        if (rev[i] > rot[i]) { break; }
    }
    if (use_rev) memcpy(out, rev, len * sizeof(int)); else memcpy(out, rot, len * sizeof(int));
}

/* ================================================================
 * Hash set for cycle deduplication
 * ================================================================ */
typedef struct HashEntry {
    int cycle[MAX_CYC];
    int len;
    struct HashEntry *next;
} HashEntry;

typedef struct {
    HashEntry **buckets;
    int size;
    int count;
} HashSet;

static uint64_t hash_cycle(const int *c, int len) {
    uint64_t h = 14695981039346656037ULL;
    int i;
    for (i = 0; i < len; i++) {
        h ^= (uint64_t)(unsigned int)c[i];
        h *= 1099511628211ULL;
    }
    return h;
}

static HashSet *hashset_new(int size) {
    HashSet *hs = (HashSet *)calloc(1, sizeof(HashSet));
    hs->size = size;
    hs->buckets = (HashEntry **)calloc(size, sizeof(HashEntry *));
    return hs;
}

static int hashset_insert(HashSet *hs, const int *cycle, int len) {
    uint64_t h = hash_cycle(cycle, len) % (uint64_t)hs->size;
    HashEntry *e = hs->buckets[h];
    while (e) {
        if (e->len == len && memcmp(e->cycle, cycle, len * sizeof(int)) == 0)
            return 0; /* already exists */
        e = e->next;
    }
    e = (HashEntry *)malloc(sizeof(HashEntry));
    memcpy(e->cycle, cycle, len * sizeof(int));
    e->len = len;
    e->next = hs->buckets[h];
    hs->buckets[h] = e;
    hs->count++;
    return 1;
}

static void hashset_free(HashSet *hs) {
    int i;
    for (i = 0; i < hs->size; i++) {
        HashEntry *e = hs->buckets[i];
        while (e) {
            HashEntry *next = e->next;
            free(e);
            e = next;
        }
    }
    free(hs->buckets);
    free(hs);
}

/* ================================================================
 * Cycle collector (one hash set per cycle length)
 * ================================================================ */
typedef struct {
    HashSet *sets[MAX_CYC + 1];  /* sets[3], sets[4], sets[5] */
    int max_length;
} Collector;

static void collector_init(Collector *c, int max_length, int hash_size) {
    int i;
    c->max_length = max_length;
    for (i = 0; i <= MAX_CYC; i++) {
        c->sets[i] = (i >= 3 && i <= max_length)
            ? hashset_new(hash_size) : NULL;
    }
}

static void collector_free(Collector *c) {
    int i;
    for (i = 0; i <= MAX_CYC; i++)
        if (c->sets[i]) hashset_free(c->sets[i]);
}

static void record_cycle(Collector *col, int li,
                         const int *path, int path_len_with_li) {
    /*
     * path = [lj, ..., li]  (path_len_with_li elements, li at end)
     * cycle = [li] + path   (path_len_with_li + 1 elements)
     * clen = path_len_with_li  (dict key = cycle length WITHOUT closing node)
     *
     * This matches the Python BFS: clen = depth + 1, cycle has clen+1 elements.
     */
    int clen = path_len_with_li;
    int cycle_arr_len = path_len_with_li + 1;
    int cycle[MAX_CYC], canonical[MAX_CYC];

    if (clen < 3 || clen > col->max_length) return;
    if (!col->sets[clen]) return;
    if (cycle_arr_len > MAX_CYC) return;

    cycle[0] = li;
    memcpy(cycle + 1, path, path_len_with_li * sizeof(int));
    cycle_canonicalize(cycle, cycle_arr_len, canonical);
    hashset_insert(col->sets[clen], canonical, cycle_arr_len);
}

/* ================================================================
 * DFS cycle search
 * ================================================================ */
static void dfs(int current, int li,
                int *visited, int *path, int path_len,
                int max_length,
                const int *adj_flat, const int *adj_off, const int *adj_sz,
                Collector *col) {
    int i, start = adj_off[current];
    int count = adj_sz[current];

    for (i = 0; i < count; i++) {
        int nbr = adj_flat[start + i];

        /* First step from lj: skip li (no 2-cycles) */
        if (path_len == 1 && nbr == li) continue;

        /* Found cycle back to li */
        if (nbr == li && path_len >= 2) {
            path[path_len] = li;  /* append li to path */
            record_cycle(col, li, path, path_len + 1);
            continue;
        }

        /* Skip visited (includes lj and all intermediate nodes) */
        if (visited[nbr]) continue;

        /* Depth limit: can still find li next step if path_len < max_length-1 */
        if (path_len >= max_length - 1) continue;

        /* Recurse */
        visited[nbr] = 1;
        path[path_len] = nbr;
        dfs(nbr, li, visited, path, path_len + 1,
            max_length, adj_flat, adj_off, adj_sz, col);
        visited[nbr] = 0;
    }
}

/* ================================================================
 * Python interface
 * ================================================================ */
static PyObject *py_find_all_cycles(PyObject *self, PyObject *args) {
    PyObject *py_adj_flat, *py_adj_off, *py_adj_sz, *py_edges;
    int n_nodes, max_length;
    Py_ssize_t i, adj_total, n_edges;
    int *adj_flat, *adj_off, *adj_sz, *visited, *path;
    Collector col;

    if (!PyArg_ParseTuple(args, "OOOOii",
            &py_adj_flat, &py_adj_off, &py_adj_sz,
            &py_edges, &n_nodes, &max_length))
        return NULL;

    /* Convert Python lists to C arrays */
    adj_total = PyList_Size(py_adj_flat);
    adj_flat = (int *)malloc(adj_total * sizeof(int));
    for (i = 0; i < adj_total; i++)
        adj_flat[i] = (int)PyLong_AsLong(PyList_GET_ITEM(py_adj_flat, i));

    adj_off = (int *)malloc(n_nodes * sizeof(int));
    adj_sz  = (int *)malloc(n_nodes * sizeof(int));
    for (i = 0; i < n_nodes; i++) {
        adj_off[i] = (int)PyLong_AsLong(PyList_GET_ITEM(py_adj_off, i));
        adj_sz[i]  = (int)PyLong_AsLong(PyList_GET_ITEM(py_adj_sz, i));
    }

    n_edges = PyList_Size(py_edges);

    /* Allocate working memory */
    visited = (int *)calloc(n_nodes, sizeof(int));
    path = (int *)malloc((max_length + 2) * sizeof(int));

    int hash_size = (int)(n_edges * 4);
    if (hash_size < 4096) hash_size = 4096;
    collector_init(&col, max_length, hash_size);

    /* Main loop: for each edge (li, lj) */
    for (i = 0; i < n_edges; i++) {
        PyObject *edge = PyList_GET_ITEM(py_edges, i);
        int li = (int)PyLong_AsLong(PyTuple_GET_ITEM(edge, 0));
        int lj = (int)PyLong_AsLong(PyTuple_GET_ITEM(edge, 1));

        memset(visited, 0, n_nodes * sizeof(int));
        visited[lj] = 1;
        path[0] = lj;

        dfs(lj, li, visited, path, 1, max_length,
            adj_flat, adj_off, adj_sz, &col);
    }

    /* Build Python result: {int: list of list} */
    PyObject *result = PyDict_New();
    int k;
    for (k = 3; k <= max_length; k++) {
        HashSet *hs;
        PyObject *py_list;
        int b;

        if (!col.sets[k]) continue;
        hs = col.sets[k];
        py_list = PyList_New(0);

        for (b = 0; b < hs->size; b++) {
            HashEntry *entry = hs->buckets[b];
            while (entry) {
                int j;
                PyObject *inner = PyList_New(entry->len);
                for (j = 0; j < entry->len; j++)
                    PyList_SET_ITEM(inner, j, PyLong_FromLong(entry->cycle[j]));
                PyList_Append(py_list, inner);
                Py_DECREF(inner);
                entry = entry->next;
            }
        }

        PyObject *py_key = PyLong_FromLong(k);
        PyDict_SetItem(result, py_key, py_list);
        Py_DECREF(py_key);
        Py_DECREF(py_list);
    }

    /* Cleanup */
    free(adj_flat); free(adj_off); free(adj_sz);
    free(visited); free(path);
    collector_free(&col);

    return result;
}

/* Module definition */
static PyMethodDef methods[] = {
    {"find_all_cycles_c", py_find_all_cycles, METH_VARARGS,
     "Find all cycles (C implementation). Same output as GenesisState.find_all_cycles."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT, "_cycle_finder",
    "Accelerated cycle finder for ESDE Genesis", -1, methods
};

PyMODINIT_FUNC PyInit__cycle_finder(void) {
    return PyModule_Create(&module_def);
}
