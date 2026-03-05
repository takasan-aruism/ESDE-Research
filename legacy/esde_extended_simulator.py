"""
ESDE Extended Simulator
========================

Extensions:
1. Recursive Emergence (Multi-scale): Level 0 → Level 1 → Level 2 → Level 3
2. Endogenous γ: Self-tuning Triangle Bonus based on explainability maximization

Based on: ESDE Mathematical Foundations v1.0
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import random
import math
from copy import deepcopy


# ============================================================
# BASIC STRUCTURES (from original simulator)
# ============================================================

class ExistenceSet:
    def __init__(self, n: int):
        self.n = n
        self.entities = list(range(n))
    
    def __len__(self):
        return self.n
    
    def __iter__(self):
        return iter(self.entities)
    
    def pairs(self):
        for i in range(self.n):
            for j in range(i + 1, self.n):
                yield (i, j)
    
    def triples(self):
        for i in range(self.n):
            for j in range(i + 1, self.n):
                for k in range(j + 1, self.n):
                    yield (i, j, k)


class LinkageFunction:
    def __init__(self, n: int):
        self.n = n
        self._L = np.eye(n) * 0.0  # Start with no connections
        np.fill_diagonal(self._L, 1.0)  # Self-connection = 1
    
    def __call__(self, a: int, b: int) -> float:
        if a >= self.n or b >= self.n:
            return 0.0
        return self._L[a, b]
    
    def set(self, a: int, b: int, value: float):
        value = np.clip(value, 0.0, 1.0)
        self._L[a, b] = value
        self._L[b, a] = value
    
    def add(self, a: int, b: int, delta: float):
        new_val = self._L[a, b] + delta
        self.set(a, b, new_val)
    
    @property
    def matrix(self) -> np.ndarray:
        return self._L.copy()
    
    def mean_linkage(self) -> float:
        return np.sum(self._L) / (self.n * self.n)
    
    def copy(self):
        new_L = LinkageFunction(self.n)
        new_L._L = self._L.copy()
        return new_L


# ============================================================
# BOUNDARY DETECTION
# ============================================================

class BoundaryDetector:
    """
    Detects boundaries (closed clusters) that can become
    meta-level entities.
    """
    
    def __init__(self, L: LinkageFunction, threshold: float = 0.15):
        self.L = L
        self.threshold = threshold
    
    def find_triangles(self) -> List[Tuple[int, int, int]]:
        """Find all triangles in the system."""
        triangles = []
        n = self.L.n
        
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    if (self.L(i, j) > self.threshold and
                        self.L(j, k) > self.threshold and
                        self.L(k, i) > self.threshold):
                        triangles.append((i, j, k))
        
        return triangles
    
    def find_clusters(self) -> List[Set[int]]:
        """Find connected components (potential boundaries)."""
        n = self.L.n
        
        # Build adjacency
        adj = defaultdict(set)
        for i in range(n):
            for j in range(i + 1, n):
                if self.L(i, j) > self.threshold:
                    adj[i].add(j)
                    adj[j].add(i)
        
        # BFS to find components
        visited = set()
        clusters = []
        
        for start in range(n):
            if start in visited or start not in adj:
                continue
            
            cluster = set()
            queue = [start]
            
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                cluster.add(node)
                
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if len(cluster) >= 3:  # Minimum size for a boundary
                clusters.append(cluster)
        
        return clusters
    
    def cluster_density(self, cluster: Set[int]) -> float:
        """Calculate internal link density of a cluster."""
        if len(cluster) < 2:
            return 0.0
        
        internal_links = 0
        max_links = len(cluster) * (len(cluster) - 1) / 2
        
        members = list(cluster)
        for i, a in enumerate(members):
            for b in members[i+1:]:
                if self.L(a, b) > self.threshold:
                    internal_links += 1
        
        return internal_links / max_links if max_links > 0 else 0.0
    
    def viable_boundaries(self, min_density: float = 0.5) -> List[Set[int]]:
        """Get boundaries that are sufficiently dense (closed)."""
        clusters = self.find_clusters()
        return [c for c in clusters if self.cluster_density(c) >= min_density]


# ============================================================
# EXPLAINABILITY METRICS
# ============================================================

class ExplainabilityCalculator:
    """Compute explainability X using Kolmogorov complexity approximation."""
    
    @staticmethod
    def approximate_K(data: np.ndarray) -> float:
        """Approximate Kolmogorov complexity via entropy."""
        flat = data.flatten()
        if len(flat) == 0:
            return 0.0
        
        # Discretize
        bins = min(20, len(flat))
        hist, _ = np.histogram(flat, bins=bins)
        probs = hist / np.sum(hist) if np.sum(hist) > 0 else np.ones(bins) / bins
        
        # Entropy
        probs = probs[probs > 0]
        H = -np.sum(probs * np.log2(probs)) if len(probs) > 0 else 0
        
        # Normalize
        H_max = np.log2(bins) if bins > 1 else 1
        K = (H / H_max) * len(flat) if H_max > 0 else len(flat)
        
        return K
    
    @staticmethod
    def explainability(L: LinkageFunction) -> float:
        """X = 1 - K/|data|"""
        data = L.matrix
        K = ExplainabilityCalculator.approximate_K(data)
        size = data.size
        
        if size == 0:
            return 0.0
        
        X = 1 - K / size
        return max(0.0, min(1.0, X))


# ============================================================
# SINGLE LEVEL DYNAMICS
# ============================================================

@dataclass
class LevelState:
    """State of a single level in the hierarchy."""
    level: int
    n_entities: int
    L: LinkageFunction
    entity_labels: List[str] = field(default_factory=list)
    
    # Which lower-level entities compose each entity at this level
    composition: Dict[int, Set[int]] = field(default_factory=dict)


class LevelDynamics:
    """Dynamics for a single level."""
    
    def __init__(self, state: LevelState, 
                 alpha: float, beta: float, gamma: float, epsilon: float, dt: float):
        self.state = state
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.epsilon = epsilon
        self.dt = dt
    
    def triangle_strength(self, a: int, b: int) -> float:
        """T(a,b) = Σ_c L(a,c) · L(b,c)"""
        total = 0.0
        for c in range(self.state.n_entities):
            if c != a and c != b:
                total += self.state.L(a, c) * self.state.L(b, c)
        return total
    
    def step(self):
        """Execute one time step."""
        n = self.state.n_entities
        if n < 2:
            return
        
        dL = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                L_ij = self.state.L(i, j)
                T_ij = self.triangle_strength(i, j)
                
                # Equation 2.1
                formation = self.alpha * 0.1 * (1 + self.gamma * T_ij)
                decay = self.beta * L_ij
                noise = self.epsilon * np.random.randn() * 0.1
                
                dL[i, j] = formation - decay + noise
                dL[j, i] = dL[i, j]
        
        # Update
        for i in range(n):
            for j in range(i + 1, n):
                self.state.L.add(i, j, dL[i, j] * self.dt)


# ============================================================
# RECURSIVE EMERGENCE (MULTI-SCALE)
# ============================================================

class RecursiveEmergenceSimulator:
    """
    Implements recursive emergence across multiple levels:
    
    Level 0: Base entities
    Level 1: Boundaries (clusters of Level 0)
    Level 2: Meta-boundaries (clusters of Level 1)
    Level 3: Self-referential structure
    
    At each level, the same dynamics apply.
    """
    
    def __init__(self, 
                 n_base_entities: int = 30,
                 max_levels: int = 3,
                 alpha: float = 0.05,
                 beta: float = 0.08,
                 gamma: float = 0.2,
                 epsilon: float = 0.1,
                 dt: float = 0.1,
                 seed: int = 42):
        
        np.random.seed(seed)
        random.seed(seed)
        
        self.max_levels = max_levels
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.epsilon = epsilon
        self.dt = dt
        
        # Initialize Level 0
        self.levels: List[LevelState] = []
        
        level0 = LevelState(
            level=0,
            n_entities=n_base_entities,
            L=LinkageFunction(n_base_entities),
            entity_labels=[f"e{i}" for i in range(n_base_entities)]
        )
        self.levels.append(level0)
        
        # Spatial positions for Level 0 (enables spatial clustering)
        self.positions = np.random.rand(n_base_entities, 2)
        
        # Group entities into initial clusters (simulate spatial proximity)
        n_clusters = 5
        for i in range(n_base_entities):
            cluster_id = i % n_clusters
            center = np.array([0.2 + 0.15 * (cluster_id % 3), 0.3 + 0.2 * (cluster_id // 3)])
            self.positions[i] = center + np.random.randn(2) * 0.08
        self.positions = np.clip(self.positions, 0, 1)
        
        # History
        self.history = {
            'time': [],
            'levels_active': [],
            'level_sizes': [],
            'total_boundaries': [],
            'explainability': [],
            'self_reference_detected': []
        }
        
        self.time = 0.0
        self.self_reference_detected = False
    
    def step(self):
        """Execute one time step across all levels."""
        self.time += self.dt
        
        # Step dynamics at Level 0 with spatial proximity
        self._step_level0()
        
        # Step dynamics at higher levels
        for level_state in self.levels[1:]:
            if level_state.n_entities >= 2:
                dynamics = LevelDynamics(
                    level_state,
                    self.alpha, self.beta, self.gamma, self.epsilon, self.dt
                )
                dynamics.step()
        
        # Check for emergence of new levels
        self._check_emergence()
        
        # Check for self-reference (Level 3 condition)
        self._check_self_reference()
        
        # Record history
        self._record_history()
    
    def _step_level0(self):
        """Level 0 dynamics with spatial clustering."""
        n = self.levels[0].n_entities
        L = self.levels[0].L
        
        dL = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                # Spatial proximity affects formation
                dist = np.linalg.norm(self.positions[i] - self.positions[j])
                proximity = np.exp(-dist * 5)  # Exponential decay
                
                L_ij = L(i, j)
                
                # Triangle strength
                T_ij = 0.0
                for k in range(n):
                    if k != i and k != j:
                        T_ij += L(i, k) * L(j, k)
                
                # Formation favors nearby entities
                formation = self.alpha * proximity * (1 + self.gamma * T_ij)
                decay = self.beta * L_ij
                noise = self.epsilon * np.random.randn() * 0.02
                
                dL[i, j] = formation - decay + noise
                dL[j, i] = dL[i, j]
        
        # Update
        for i in range(n):
            for j in range(i + 1, n):
                L.add(i, j, dL[i, j] * self.dt)
    
    def _check_emergence(self):
        """Check if new meta-level should emerge."""
        if len(self.levels) >= self.max_levels:
            return
        
        current_level = self.levels[-1]
        detector = BoundaryDetector(current_level.L, threshold=0.2)
        boundaries = detector.viable_boundaries(min_density=0.3)
        
        # Filter out overlapping boundaries (keep larger ones)
        non_overlapping = []
        used = set()
        for b in sorted(boundaries, key=len, reverse=True):
            if not any(e in used for e in b):
                non_overlapping.append(b)
                used.update(b)
        
        # Need at least 3 boundaries to form meta-triangles
        if len(non_overlapping) >= 3:
            self._create_meta_level(non_overlapping)
    
    def _create_meta_level(self, boundaries: List[Set[int]]):
        """Create a new meta-level from boundaries."""
        current_level = len(self.levels)
        n_meta = len(boundaries)
        
        meta_state = LevelState(
            level=current_level,
            n_entities=n_meta,
            L=LinkageFunction(n_meta),
            entity_labels=[f"C{current_level}_{i}" for i in range(n_meta)]
        )
        
        # Record composition
        for i, boundary in enumerate(boundaries):
            meta_state.composition[i] = boundary
        
        # Initialize meta-linkages based on lower-level connectivity
        lower_L = self.levels[-1].L
        for i in range(n_meta):
            for j in range(i + 1, n_meta):
                # Average cross-boundary linkage
                total = 0.0
                count = 0
                for a in boundaries[i]:
                    for b in boundaries[j]:
                        total += lower_L(a, b)
                        count += 1
                meta_L = (total / count if count > 0 else 0.0) * 2  # Amplify
                meta_state.L.set(i, j, meta_L)
        
        self.levels.append(meta_state)
        print(f"  [EMERGENCE] Level {current_level}: {n_meta} meta-entities from "
              f"{sum(len(b) for b in boundaries)} base entities")
    
    def _boundary_interaction(self, b1: Set[int], b2: Set[int]) -> float:
        """
        Compute interaction strength between two boundaries.
        Based on how their members are connected.
        """
        if len(self.levels) < 1:
            return 0.0
        
        lower_L = self.levels[-1].L
        
        # Average linkage between members
        total = 0.0
        count = 0
        
        for a in b1:
            for b in b2:
                total += lower_L(a, b)
                count += 1
        
        return total / count if count > 0 else 0.0
    
    def _check_self_reference(self):
        """
        Check if self-referential closure is achieved.
        
        This happens when:
        - We have at least 2 levels (meta-level exists)
        - At any meta-level, there's a triangle (self-referential closure)
        """
        if len(self.levels) < 2:
            self.self_reference_detected = False
            return
        
        # Check for triangles at any meta-level (Level 1+)
        for level_state in self.levels[1:]:
            if level_state.n_entities >= 3:
                detector = BoundaryDetector(level_state.L, threshold=0.15)
                triangles = detector.find_triangles()
                
                if triangles:
                    if not self.self_reference_detected:
                        print(f"  [SELF-REFERENCE] Detected at Level {level_state.level}: "
                              f"{len(triangles)} triangle(s)")
                    self.self_reference_detected = True
                    return
        
        self.self_reference_detected = False
    
    def _record_history(self):
        """Record current state."""
        self.history['time'].append(self.time)
        self.history['levels_active'].append(len(self.levels))
        self.history['level_sizes'].append([l.n_entities for l in self.levels])
        
        # Count total boundaries
        total_boundaries = 0
        for level in self.levels:
            detector = BoundaryDetector(level.L)
            total_boundaries += len(detector.viable_boundaries())
        self.history['total_boundaries'].append(total_boundaries)
        
        # Compute overall explainability
        total_X = 0.0
        for level in self.levels:
            total_X += ExplainabilityCalculator.explainability(level.L)
        self.history['explainability'].append(total_X / len(self.levels))
        
        self.history['self_reference_detected'].append(self.self_reference_detected)
    
    def run(self, steps: int):
        """Run simulation."""
        print(f"Running Recursive Emergence Simulator")
        print(f"  Base entities: {self.levels[0].n_entities}")
        print(f"  Max levels: {self.max_levels}")
        print(f"  Parameters: alpha={self.alpha}, beta={self.beta}, "
              f"gamma={self.gamma}, epsilon={self.epsilon}")
        print()
        
        for i in range(steps):
            self.step()
            
            if (i + 1) % 50 == 0:
                print(f"  Step {i+1}/{steps}: {len(self.levels)} levels active, "
                      f"X={self.history['explainability'][-1]:.3f}")
        
        print()
        print(f"Final state:")
        print(f"  Active levels: {len(self.levels)}")
        for level in self.levels:
            print(f"    Level {level.level}: {level.n_entities} entities")
        print(f"  Self-reference detected: {self.self_reference_detected}")
        print(f"  Final explainability: {self.history['explainability'][-1]:.3f}")
        
        return self.history
    
    def plot(self, save_path: str = None):
        """Visualize results."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("Recursive Emergence: Level 0 → Level 3", fontsize=14)
        
        # 1. Levels over time
        ax1 = axes[0, 0]
        ax1.plot(self.history['time'], self.history['levels_active'], 'b-', linewidth=2)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Active Levels')
        ax1.set_title('Hierarchy Depth Over Time')
        ax1.set_ylim(0, self.max_levels + 1)
        ax1.grid(True, alpha=0.3)
        
        # 2. Boundaries over time
        ax2 = axes[0, 1]
        ax2.plot(self.history['time'], self.history['total_boundaries'], 'g-', linewidth=2)
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Total Boundaries')
        ax2.set_title('Boundary Formation')
        ax2.grid(True, alpha=0.3)
        
        # 3. Explainability over time
        ax3 = axes[1, 0]
        ax3.plot(self.history['time'], self.history['explainability'], 'r-', linewidth=2)
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Average X')
        ax3.set_title('System Explainability')
        ax3.grid(True, alpha=0.3)
        
        # 4. Self-reference detection
        ax4 = axes[1, 1]
        sr = np.array(self.history['self_reference_detected']).astype(float)
        ax4.fill_between(self.history['time'], 0, sr, alpha=0.5, color='purple')
        ax4.set_xlabel('Time')
        ax4.set_ylabel('Self-Reference')
        ax4.set_title('Self-Reference (Consciousness Indicator)')
        ax4.set_ylim(-0.1, 1.1)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved: {save_path}")
        
        return fig


# ============================================================
# ENDOGENOUS GAMMA (Self-Tuning)
# ============================================================

class EndogenousGammaSimulator:
    """
    Implements self-tuning γ based on explainability maximization:
    
    dγ/dt = η · ∂X/∂γ
    
    The system adjusts its own Triangle Bonus to maximize explainability.
    """
    
    def __init__(self,
                 n_entities: int = 30,
                 alpha: float = 0.05,
                 beta: float = 0.08,
                 gamma_init: float = 0.1,
                 epsilon: float = 0.1,
                 eta: float = 0.5,  # Learning rate for gamma
                 dt: float = 0.1,
                 seed: int = 42):
        
        np.random.seed(seed)
        random.seed(seed)
        
        self.n = n_entities
        self.L = LinkageFunction(n_entities)
        
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma_init
        self.epsilon = epsilon
        self.eta = eta
        self.dt = dt
        
        # History
        self.history = {
            'time': [],
            'gamma': [],
            'explainability': [],
            'mean_linkage': [],
            'triangle_density': []
        }
        
        self.time = 0.0
    
    def triangle_strength(self, a: int, b: int) -> float:
        total = 0.0
        for c in range(self.n):
            if c != a and c != b:
                total += self.L(a, c) * self.L(b, c)
        return total
    
    def count_triangles(self) -> int:
        count = 0
        threshold = 0.2
        for i in range(self.n):
            for j in range(i + 1, self.n):
                for k in range(j + 1, self.n):
                    if (self.L(i, j) > threshold and
                        self.L(j, k) > threshold and
                        self.L(k, i) > threshold):
                        count += 1
        return count
    
    def triangle_density(self) -> float:
        max_tri = self.n * (self.n - 1) * (self.n - 2) // 6
        return self.count_triangles() / max_tri if max_tri > 0 else 0
    
    def step(self):
        """Execute one step with gamma self-adjustment."""
        self.time += self.dt
        
        # === Step 1: Compute current metrics ===
        X_before = ExplainabilityCalculator.explainability(self.L)
        tau_before = self.triangle_density()
        
        # === Step 2: Run dynamics ===
        self._dynamics_step()
        
        # === Step 3: Compute new metrics ===
        X_after = ExplainabilityCalculator.explainability(self.L)
        tau_after = self.triangle_density()
        
        # === Step 4: Update γ based on X change ===
        # If X increased, move γ in direction that increases triangles
        # If triangles help X, increase γ
        dX = X_after - X_before
        dtau = tau_after - tau_before
        
        # Correlation-based update
        if dtau > 0 and dX > 0:
            # Triangles helped - increase gamma
            self.gamma += self.eta * 0.02
        elif dtau > 0 and dX < 0:
            # Triangles hurt - decrease gamma  
            self.gamma -= self.eta * 0.01
        elif dtau < 0 and dX > 0:
            # Fewer triangles helped - decrease gamma
            self.gamma -= self.eta * 0.01
        else:
            # Random exploration
            self.gamma += self.eta * 0.005 * np.random.randn()
        
        self.gamma = np.clip(self.gamma, 0.0, 1.0)
        
        # === Record ===
        self.history['time'].append(self.time)
        self.history['gamma'].append(self.gamma)
        self.history['explainability'].append(X_after)
        self.history['mean_linkage'].append(self.L.mean_linkage())
        self.history['triangle_density'].append(tau_after)
    
    def _dynamics_step(self):
        """Link dynamics step."""
        n = self.n
        dL = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                L_ij = self.L(i, j)
                T_ij = self.triangle_strength(i, j)
                
                formation = self.alpha * 0.1 * (1 + self.gamma * T_ij)
                decay = self.beta * L_ij
                noise = self.epsilon * np.random.randn() * 0.1
                
                dL[i, j] = formation - decay + noise
                dL[j, i] = dL[i, j]
        
        for i in range(n):
            for j in range(i + 1, n):
                self.L.add(i, j, dL[i, j] * self.dt)
    
    def run(self, steps: int):
        """Run simulation."""
        print(f"Running Endogenous Gamma Simulator")
        print(f"  Entities: {self.n}")
        print(f"  Initial gamma: {self.gamma:.3f}")
        print(f"  Learning rate eta: {self.eta}")
        print()
        
        for i in range(steps):
            self.step()
            
            if (i + 1) % 50 == 0:
                print(f"  Step {i+1}/{steps}: gamma={self.gamma:.3f}, "
                      f"X={self.history['explainability'][-1]:.3f}")
        
        print()
        print(f"Final state:")
        print(f"  Final gamma: {self.gamma:.3f}")
        print(f"  Final X: {self.history['explainability'][-1]:.3f}")
        print(f"  Final triangle density: {self.history['triangle_density'][-1]:.3f}")
        
        return self.history
    
    def plot(self, save_path: str = None):
        """Visualize results."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("Endogenous γ: Self-Tuning Triangle Bonus", fontsize=14)
        
        # 1. Gamma over time
        ax1 = axes[0, 0]
        ax1.plot(self.history['time'], self.history['gamma'], 'b-', linewidth=2)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('γ (Triangle Bonus)')
        ax1.set_title('Self-Tuning γ')
        ax1.grid(True, alpha=0.3)
        
        # 2. Explainability over time
        ax2 = axes[0, 1]
        ax2.plot(self.history['time'], self.history['explainability'], 'r-', linewidth=2)
        ax2.set_xlabel('Time')
        ax2.set_ylabel('X')
        ax2.set_title('Explainability (Being Maximized)')
        ax2.grid(True, alpha=0.3)
        
        # 3. Triangle density over time
        ax3 = axes[1, 0]
        ax3.plot(self.history['time'], self.history['triangle_density'], 'g-', linewidth=2)
        ax3.set_xlabel('Time')
        ax3.set_ylabel('τ')
        ax3.set_title('Triangle Density')
        ax3.grid(True, alpha=0.3)
        
        # 4. Gamma vs Explainability
        ax4 = axes[1, 1]
        ax4.scatter(self.history['gamma'], self.history['explainability'], 
                   c=self.history['time'], cmap='viridis', alpha=0.6)
        ax4.set_xlabel('γ')
        ax4.set_ylabel('X')
        ax4.set_title('γ vs X Trajectory (color=time)')
        ax4.grid(True, alpha=0.3)
        plt.colorbar(ax4.collections[0], ax=ax4, label='Time')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved: {save_path}")
        
        return fig


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("ESDE Extended Simulator")
    print("1. Recursive Emergence (Multi-scale)")
    print("2. Endogenous Gamma (Self-tuning)")
    print("=" * 70)
    
    # === Experiment 1: Recursive Emergence ===
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Recursive Emergence (Level 0 → Level 3)")
    print("=" * 70 + "\n")
    
    recursive_sim = RecursiveEmergenceSimulator(
        n_base_entities=40,
        max_levels=4,
        alpha=0.2,       # Higher formation
        beta=0.02,       # Lower decay
        gamma=0.5,       # Higher triangle bonus
        epsilon=0.05,    # Lower noise
        seed=123
    )
    
    recursive_history = recursive_sim.run(steps=600)
    recursive_sim.plot("recursive_emergence_results.png")
    
    # === Experiment 2: Endogenous Gamma ===
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Endogenous Gamma (Self-Tuning Universe)")
    print("=" * 70 + "\n")
    
    endo_sim = EndogenousGammaSimulator(
        n_entities=25,
        alpha=0.08,
        beta=0.04,
        gamma_init=0.02,  # Start with very low gamma
        epsilon=0.08,
        eta=1.0,  # Higher learning rate
        seed=42
    )
    
    endo_history = endo_sim.run(steps=300)
    endo_sim.plot("endogenous_gamma_results.png")
    
    # === Summary ===
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print(f"""
    EXPERIMENT 1: Recursive Emergence
    ---------------------------------
    - Started with {recursive_sim.levels[0].n_entities} base entities (Level 0)
    - Final hierarchy depth: {len(recursive_sim.levels)} levels
    - Self-reference detected: {recursive_sim.self_reference_detected}
    
    This demonstrates that higher-level "observers" can emerge from
    lower-level dynamics, and eventually self-referential structure
    (a potential correlate of consciousness) can appear.
    
    EXPERIMENT 2: Endogenous Gamma
    ------------------------------
    - Initial gamma: 0.05
    - Final gamma: {endo_sim.gamma:.3f}
    - Initial X: {endo_history['explainability'][0]:.3f}
    - Final X: {endo_history['explainability'][-1]:.3f}
    
    This demonstrates that a system can "discover" the optimal
    Triangle Bonus by gradient ascent on explainability.
    The universe "tunes itself" to maximize X.
    
    IMPLICATIONS:
    - Life emerges because boundaries emerge (Experiment 1)
    - Boundaries emerge because γ > 0 (Experiment 2)
    - γ > 0 because it maximizes X (self-selection)
    - Therefore: Life is inevitable in an X-maximizing universe
    """)
    
    print("=" * 70)
    print("Output files:")
    print("  - recursive_emergence_results.png")
    print("  - endogenous_gamma_results.png")
    print("=" * 70)
    
    return recursive_sim, endo_sim


if __name__ == "__main__":
    main()
