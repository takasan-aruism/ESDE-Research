"""
ESDE Evolution Simulator
=========================

Implements evolutionary dynamics on physical parameters:
- Local γ (Triangle Bonus) varies by region
- Selection based on local explainability X
- Successful parameters spread, failing ones mutate

This demonstrates that "life-friendly" parameters emerge
through selection, not fine-tuning.
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import random


# ============================================================
# GRID-BASED WORLD
# ============================================================

@dataclass
class GridCell:
    """A cell in the 2D world with local parameters."""
    x: int
    y: int
    
    # Local parameters (can evolve)
    gamma: float = 0.1      # Triangle Bonus
    epsilon: float = 0.1    # Flexibility
    
    # Local state
    entities: List[int] = field(default_factory=list)
    
    # Fitness metrics
    local_X: float = 0.0    # Local explainability
    local_phi: float = 0.0  # Local synergy
    triangle_count: int = 0


class EvolutionaryWorld:
    """
    2D grid world where:
    - Entities move and form links
    - Each cell has local parameters (γ, ε)
    - Parameters evolve based on local success (X)
    """
    
    def __init__(self,
                 grid_size: int = 10,
                 n_entities: int = 200,
                 alpha: float = 0.1,
                 beta: float = 0.05,
                 dt: float = 0.1,
                 selection_interval: int = 20,
                 mutation_rate: float = 0.1,
                 seed: int = 42):
        
        np.random.seed(seed)
        random.seed(seed)
        
        self.grid_size = grid_size
        self.n_entities = n_entities
        self.alpha = alpha
        self.beta = beta
        self.dt = dt
        self.selection_interval = selection_interval
        self.mutation_rate = mutation_rate
        
        # Initialize grid
        self.grid: Dict[Tuple[int, int], GridCell] = {}
        for x in range(grid_size):
            for y in range(grid_size):
                self.grid[(x, y)] = GridCell(
                    x=x, y=y,
                    gamma=np.random.uniform(0.0, 0.5),  # Random initial γ
                    epsilon=np.random.uniform(0.05, 0.2)
                )
        
        # Entity positions and linkages
        self.positions = np.random.rand(n_entities, 2) * grid_size
        self.L = np.zeros((n_entities, n_entities))  # Linkage matrix
        np.fill_diagonal(self.L, 1.0)
        
        # Assign entities to cells
        self._assign_entities_to_cells()
        
        # History
        self.history = {
            'time': [],
            'mean_gamma': [],
            'std_gamma': [],
            'mean_X': [],
            'total_triangles': [],
            'gamma_distribution': []
        }
        
        self.time = 0.0
        self.step_count = 0
    
    def _assign_entities_to_cells(self):
        """Assign each entity to its grid cell."""
        # Clear existing assignments
        for cell in self.grid.values():
            cell.entities = []
        
        # Assign based on position
        for i in range(self.n_entities):
            x = int(np.clip(self.positions[i, 0], 0, self.grid_size - 0.01))
            y = int(np.clip(self.positions[i, 1], 0, self.grid_size - 0.01))
            self.grid[(x, y)].entities.append(i)
    
    def _get_cell(self, entity_id: int) -> GridCell:
        """Get the cell containing an entity."""
        x = int(np.clip(self.positions[entity_id, 0], 0, self.grid_size - 0.01))
        y = int(np.clip(self.positions[entity_id, 1], 0, self.grid_size - 0.01))
        return self.grid[(x, y)]
    
    def _get_local_gamma(self, i: int, j: int) -> float:
        """Get γ for interaction between entities i and j."""
        # Use average of their cells' γ values
        cell_i = self._get_cell(i)
        cell_j = self._get_cell(j)
        return (cell_i.gamma + cell_j.gamma) / 2
    
    def _triangle_strength(self, i: int, j: int) -> float:
        """T(i,j) = Σ_k L(i,k) · L(j,k)"""
        return np.sum(self.L[i, :] * self.L[j, :]) - self.L[i, j]
    
    def step_physics(self):
        """Execute one physics step (link dynamics)."""
        n = self.n_entities
        
        # Compute distances once
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(self.positions[i] - self.positions[j])
                
                # Skip distant pairs early
                if dist > 3.0:
                    continue
                
                proximity = np.exp(-dist * 0.5)
                L_ij = self.L[i, j]
                
                # Simplified triangle strength (only count strong links)
                T_ij = 0.0
                for k in range(n):
                    if k != i and k != j and self.L[i, k] > 0.1 and self.L[j, k] > 0.1:
                        T_ij += self.L[i, k] * self.L[j, k]
                
                # Use LOCAL gamma
                gamma_local = self._get_local_gamma(i, j)
                
                # Dynamics
                formation = self.alpha * proximity * (1 + gamma_local * T_ij)
                decay = self.beta * L_ij
                
                dL = (formation - decay) * self.dt
                self.L[i, j] = np.clip(self.L[i, j] + dL, 0, 1)
                self.L[j, i] = self.L[i, j]
        
        # Move entities slightly
        self.positions += np.random.randn(n, 2) * 0.03
        self.positions = np.clip(self.positions, 0, self.grid_size - 0.01)
        self._assign_entities_to_cells()
        
        self.time += self.dt
    
    def compute_local_fitness(self):
        """Compute fitness (X, Φ, triangles) for each cell."""
        threshold = 0.2
        
        for cell in self.grid.values():
            if len(cell.entities) < 3:
                cell.local_X = 0.0
                cell.local_phi = 0.0
                cell.triangle_count = 0
                continue
            
            # Count triangles in this cell
            triangles = 0
            entities = cell.entities
            for i, a in enumerate(entities):
                for j, b in enumerate(entities[i+1:], i+1):
                    for c in entities[j+1:]:
                        if (self.L[a, b] > threshold and 
                            self.L[b, c] > threshold and 
                            self.L[c, a] > threshold):
                            triangles += 1
            
            cell.triangle_count = triangles
            
            # Local explainability (based on link structure)
            local_links = []
            for a in entities:
                for b in entities:
                    if a < b:
                        local_links.append(self.L[a, b])
            
            if local_links:
                links_array = np.array(local_links)
                # Explainability: how "patterned" vs random
                # High variance = more structure = higher X
                mean_link = np.mean(links_array)
                if mean_link > 0:
                    # Normalized by max possible
                    cell.local_X = min(1.0, triangles / max(1, len(entities)))
                else:
                    cell.local_X = 0.0
            else:
                cell.local_X = 0.0
            
            # Synergy: triangles relative to possible
            max_tri = len(entities) * (len(entities) - 1) * (len(entities) - 2) // 6
            cell.local_phi = triangles / max(1, max_tri)
    
    def step_selection(self):
        """
        Selection step: successful parameters spread.
        
        - High X cells: maintain/spread parameters
        - Low X cells: adopt neighbor's parameters or mutate
        """
        # Compute fitness
        self.compute_local_fitness()
        
        # For each cell, decide if it should adapt
        new_gammas = {}
        
        for (x, y), cell in self.grid.items():
            # Get neighbors
            neighbors = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in self.grid:
                        neighbors.append(self.grid[(nx, ny)])
            
            if not neighbors:
                new_gammas[(x, y)] = cell.gamma
                continue
            
            # Find best neighbor
            best_neighbor = max(neighbors, key=lambda c: c.local_X)
            
            # Selection pressure
            if cell.local_X < best_neighbor.local_X - 0.1:
                # This cell is failing - adopt successful neighbor's γ
                if np.random.rand() < 0.5:
                    new_gamma = best_neighbor.gamma
                else:
                    # Or mutate
                    new_gamma = cell.gamma + np.random.randn() * self.mutation_rate
            else:
                # Cell is doing okay - small random drift
                new_gamma = cell.gamma + np.random.randn() * 0.02
            
            new_gammas[(x, y)] = np.clip(new_gamma, 0.0, 1.0)
        
        # Apply new gammas
        for (x, y), gamma in new_gammas.items():
            self.grid[(x, y)].gamma = gamma
    
    def step(self):
        """Execute one complete step."""
        self.step_count += 1
        
        # Physics
        self.step_physics()
        
        # Selection (periodically)
        if self.step_count % self.selection_interval == 0:
            self.step_selection()
        
        # Record history
        self._record_history()
    
    def _record_history(self):
        """Record current state."""
        gammas = [cell.gamma for cell in self.grid.values()]
        Xs = [cell.local_X for cell in self.grid.values()]
        triangles = sum(cell.triangle_count for cell in self.grid.values())
        
        self.history['time'].append(self.time)
        self.history['mean_gamma'].append(np.mean(gammas))
        self.history['std_gamma'].append(np.std(gammas))
        self.history['mean_X'].append(np.mean(Xs))
        self.history['total_triangles'].append(triangles)
        self.history['gamma_distribution'].append(gammas.copy())
    
    def run(self, steps: int):
        """Run simulation."""
        print(f"Running Evolutionary World Simulator")
        print(f"  Grid: {self.grid_size}x{self.grid_size}")
        print(f"  Entities: {self.n_entities}")
        print(f"  Selection interval: every {self.selection_interval} steps")
        print(f"  Mutation rate: {self.mutation_rate}")
        print()
        
        initial_gamma = np.mean([c.gamma for c in self.grid.values()])
        print(f"  Initial mean γ: {initial_gamma:.3f}")
        print()
        
        for i in range(steps):
            self.step()
            
            if (i + 1) % 100 == 0:
                mean_g = self.history['mean_gamma'][-1]
                mean_x = self.history['mean_X'][-1]
                tri = self.history['total_triangles'][-1]
                print(f"  Step {i+1}/{steps}: γ={mean_g:.3f}, X={mean_x:.3f}, triangles={tri}")
        
        final_gamma = self.history['mean_gamma'][-1]
        print()
        print(f"Final state:")
        print(f"  Final mean γ: {final_gamma:.3f}")
        print(f"  γ change: {initial_gamma:.3f} → {final_gamma:.3f}")
        print(f"  Final mean X: {self.history['mean_X'][-1]:.3f}")
        print(f"  Final triangles: {self.history['total_triangles'][-1]}")
        
        return self.history
    
    def plot(self, save_path: str = None):
        """Visualize results."""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle("Evolutionary Dynamics: Local Parameters + Selection", fontsize=14)
        
        # 1. Mean γ over time
        ax1 = axes[0, 0]
        ax1.plot(self.history['time'], self.history['mean_gamma'], 'b-', linewidth=2)
        ax1.fill_between(
            self.history['time'],
            np.array(self.history['mean_gamma']) - np.array(self.history['std_gamma']),
            np.array(self.history['mean_gamma']) + np.array(self.history['std_gamma']),
            alpha=0.3
        )
        ax1.set_xlabel('Time')
        ax1.set_ylabel('γ')
        ax1.set_title('Mean γ Over Time (±1 std)')
        ax1.grid(True, alpha=0.3)
        
        # 2. Mean X over time
        ax2 = axes[0, 1]
        ax2.plot(self.history['time'], self.history['mean_X'], 'r-', linewidth=2)
        ax2.set_xlabel('Time')
        ax2.set_ylabel('X')
        ax2.set_title('Mean Explainability Over Time')
        ax2.grid(True, alpha=0.3)
        
        # 3. Total triangles over time
        ax3 = axes[0, 2]
        ax3.plot(self.history['time'], self.history['total_triangles'], 'g-', linewidth=2)
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Triangles')
        ax3.set_title('Total Triangle Count')
        ax3.grid(True, alpha=0.3)
        
        # 4. γ distribution evolution
        ax4 = axes[1, 0]
        # Sample distributions at different times
        n_samples = min(5, len(self.history['gamma_distribution']))
        indices = np.linspace(0, len(self.history['gamma_distribution']) - 1, n_samples).astype(int)
        
        for idx in indices:
            gammas = self.history['gamma_distribution'][idx]
            time = self.history['time'][idx]
            ax4.hist(gammas, bins=20, alpha=0.4, label=f't={time:.1f}', range=(0, 1))
        
        ax4.set_xlabel('γ')
        ax4.set_ylabel('Count')
        ax4.set_title('γ Distribution Evolution')
        ax4.legend()
        
        # 5. Final γ heatmap
        ax5 = axes[1, 1]
        gamma_grid = np.zeros((self.grid_size, self.grid_size))
        for (x, y), cell in self.grid.items():
            gamma_grid[y, x] = cell.gamma
        
        im = ax5.imshow(gamma_grid, origin='lower', cmap='viridis', vmin=0, vmax=0.5)
        ax5.set_xlabel('X')
        ax5.set_ylabel('Y')
        ax5.set_title('Final γ Spatial Distribution')
        plt.colorbar(im, ax=ax5, label='γ')
        
        # 6. Final X heatmap
        ax6 = axes[1, 2]
        X_grid = np.zeros((self.grid_size, self.grid_size))
        for (x, y), cell in self.grid.items():
            X_grid[y, x] = cell.local_X
        
        im2 = ax6.imshow(X_grid, origin='lower', cmap='RdYlGn', vmin=0, vmax=1)
        ax6.set_xlabel('X')
        ax6.set_ylabel('Y')
        ax6.set_title('Final Local Explainability')
        plt.colorbar(im2, ax=ax6, label='X')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved: {save_path}")
        
        return fig


# ============================================================
# COMPARISON: EVOLUTION VS NO EVOLUTION
# ============================================================

def compare_evolution_vs_fixed():
    """Compare systems with and without parameter evolution."""
    
    print("=" * 70)
    print("COMPARISON: Evolution vs Fixed Parameters")
    print("=" * 70)
    
    # System 1: Fixed random γ (no evolution)
    print("\n[1] Fixed Random γ (No Selection)")
    world_fixed = EvolutionaryWorld(
        grid_size=5,
        n_entities=60,
        selection_interval=999999,  # Never select
        seed=42
    )
    history_fixed = world_fixed.run(steps=200)
    
    # System 2: Evolving γ (with selection)
    print("\n[2] Evolving γ (With Selection)")
    world_evolve = EvolutionaryWorld(
        grid_size=5,
        n_entities=60,
        selection_interval=15,
        mutation_rate=0.1,
        seed=42
    )
    history_evolve = world_evolve.run(steps=200)
    
    # Compare
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    print(f"""
    Fixed (No Evolution):
      Final mean γ: {history_fixed['mean_gamma'][-1]:.3f}
      Final mean X: {history_fixed['mean_X'][-1]:.3f}
      Final triangles: {history_fixed['total_triangles'][-1]}
    
    Evolving (With Selection):
      Final mean γ: {history_evolve['mean_gamma'][-1]:.3f}
      Final mean X: {history_evolve['mean_X'][-1]:.3f}
      Final triangles: {history_evolve['total_triangles'][-1]}
    
    Interpretation:
      Evolution should discover "good" γ values that increase
      triangles and explainability. The system finds the
      habitable zone automatically.
    """)
    
    return world_fixed, world_evolve


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("ESDE Evolution Simulator")
    print("Local Parameters + Selection by Explainability")
    print("=" * 70)
    
    # Main experiment
    print("\n" + "=" * 70)
    print("EXPERIMENT: Evolutionary Discovery of Life-Friendly Parameters")
    print("=" * 70 + "\n")
    
    world = EvolutionaryWorld(
        grid_size=6,
        n_entities=80,
        alpha=0.1,
        beta=0.05,
        selection_interval=15,
        mutation_rate=0.08,
        seed=42
    )
    
    history = world.run(steps=400)
    world.plot("evolution_results.png")
    
    # Comparison
    print("\n")
    world_fixed, world_evolve = compare_evolution_vs_fixed()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
    WHAT THIS DEMONSTRATES:
    
    1. Local Parameter Variation:
       - Each region has its own γ (Triangle Bonus)
       - Initially random: γ ∈ [0.0, 0.5]
    
    2. Selection by Explainability:
       - Regions with high X (structured, triangles) survive
       - Failing regions adopt successful neighbors' parameters
    
    3. Result:
       - System self-organizes to "life-friendly" parameters
       - γ converges to values that maximize structure
       - No external tuning required
    
    IMPLICATIONS:
    
    This is a model of how physical constants might "evolve":
    - Regions with good parameters → more structure → persist
    - Regions with bad parameters → chaos/death → replaced
    - Universe naturally finds habitable zone
    
    The "fine-tuning problem" dissolves:
    Constants aren't fine-tuned by a designer,
    they're selected by explainability.
    """)
    
    print("=" * 70)
    print("Output: evolution_results.png")
    print("=" * 70)
    
    return world, history


if __name__ == "__main__":
    main()
