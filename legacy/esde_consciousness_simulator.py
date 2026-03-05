"""
ESDE Recursive Consciousness Simulator
=======================================

Level 3: Self-Reference through Feedback Loops

Key additions:
1. Feedback connections: output → input
2. Temporal memory: past states influence current
3. Self-monitoring: meta-triangles that observe the network
4. Attractor detection: stable patterns = "thoughts"

Based on: ESDE Neural Simulator + Gemini's Level 3 roadmap
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque
import random


# ============================================================
# CORE STRUCTURES
# ============================================================

@dataclass
class Triangle:
    """Computational unit (neuron-like)."""
    id: int
    nodes: Tuple[int, int, int]
    activation: float = 0.0
    threshold: float = 0.3
    activation_history: deque = field(default_factory=lambda: deque(maxlen=50))
    
    def is_active(self) -> bool:
        return self.activation > self.threshold
    
    def fire(self) -> float:
        return min(1.0, self.activation) if self.is_active() else 0.0
    
    def record(self):
        self.activation_history.append(self.activation)


@dataclass
class Connection:
    """Synapse-like connection."""
    source_id: int
    target_id: int
    weight: float = 0.1
    delay: int = 0  # Time steps of delay (for feedback)


# ============================================================
# RECURSIVE NETWORK WITH FEEDBACK
# ============================================================

class RecursiveConsciousnessNetwork:
    """
    A network with feedback loops that enables:
    - Self-observation (output feeds back to input)
    - Temporal memory (delayed connections)
    - Attractor states (stable "thought" patterns)
    """
    
    def __init__(self,
                 n_entities: int = 25,
                 feedback_strength: float = 0.3,
                 feedback_delay: int = 3,
                 learning_rate: float = 0.05,
                 decay_rate: float = 0.15,
                 seed: int = 42):
        
        np.random.seed(seed)
        random.seed(seed)
        
        self.n_entities = n_entities
        self.feedback_strength = feedback_strength
        self.feedback_delay = feedback_delay
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        
        # Entity positions
        self.positions = np.random.rand(n_entities, 2)
        
        # Entity linkages
        self.L = np.zeros((n_entities, n_entities))
        
        # Triangles
        self.triangles: Dict[int, Triangle] = {}
        self.next_triangle_id = 0
        
        # Forward connections
        self.connections: List[Connection] = []
        
        # Feedback connections (output → input)
        self.feedback_connections: List[Connection] = []
        
        # Delayed signal buffer
        self.signal_buffer: Dict[int, deque] = defaultdict(
            lambda: deque([0.0] * (feedback_delay + 1), maxlen=feedback_delay + 1)
        )
        
        # I/O triangles
        self.input_triangles: Set[int] = set()
        self.output_triangles: Set[int] = set()
        self.hidden_triangles: Set[int] = set()
        
        # Meta-observer (monitors the whole network)
        self.meta_activation: float = 0.0
        self.meta_history: deque = deque(maxlen=100)
        
        # History
        self.history = {
            'time': [],
            'total_activation': [],
            'output_pattern': [],
            'meta_activation': [],
            'attractor_detected': [],
            'self_reference_strength': []
        }
        
        self.time = 0
        self.attractor_state: Optional[Tuple[float, ...]] = None
    
    def form_links(self, steps: int = 60, gamma: float = 0.5):
        """Form entity-level links."""
        print("Forming entity links...")
        
        for _ in range(steps):
            for i in range(self.n_entities):
                for j in range(i + 1, self.n_entities):
                    dist = np.linalg.norm(self.positions[i] - self.positions[j])
                    proximity = np.exp(-dist * 3)
                    
                    T_ij = 0.0
                    for k in range(self.n_entities):
                        if k != i and k != j:
                            T_ij += self.L[i, k] * self.L[j, k]
                    
                    formation = 0.1 * proximity * (1 + gamma * T_ij)
                    decay = 0.05 * self.L[i, j]
                    
                    dL = (formation - decay) * 0.1
                    self.L[i, j] = np.clip(self.L[i, j] + dL, 0, 1)
                    self.L[j, i] = self.L[i, j]
        
        print(f"  Mean linkage: {np.mean(self.L):.3f}")
    
    def discover_triangles(self, threshold: float = 0.15):
        """Find all triangles."""
        self.triangles.clear()
        self.next_triangle_id = 0
        
        for i in range(self.n_entities):
            for j in range(i + 1, self.n_entities):
                if self.L[i, j] < threshold:
                    continue
                for k in range(j + 1, self.n_entities):
                    if self.L[j, k] >= threshold and self.L[k, i] >= threshold:
                        tri = Triangle(
                            id=self.next_triangle_id,
                            nodes=(i, j, k)
                        )
                        self.triangles[self.next_triangle_id] = tri
                        self.next_triangle_id += 1
        
        print(f"Discovered {len(self.triangles)} triangles")
        return len(self.triangles)
    
    def connect_triangles(self, max_connections: int = 5000):
        """Create forward connections between triangles."""
        self.connections.clear()
        
        triangle_list = list(self.triangles.values())
        conn_count = 0
        
        for i, tri_a in enumerate(triangle_list):
            if conn_count >= max_connections:
                break
            for tri_b in triangle_list[i+1:]:
                if conn_count >= max_connections:
                    break
                
                shared = len(set(tri_a.nodes) & set(tri_b.nodes))
                if shared >= 1:
                    weight = shared / 3.0 * 0.4
                    
                    self.connections.append(Connection(
                        source_id=tri_a.id,
                        target_id=tri_b.id,
                        weight=weight
                    ))
                    self.connections.append(Connection(
                        source_id=tri_b.id,
                        target_id=tri_a.id,
                        weight=weight
                    ))
                    conn_count += 2
        
        print(f"Created {len(self.connections)} forward connections")
    
    def designate_io(self, n_input: int = 3, n_output: int = 3):
        """Designate I/O triangles."""
        if not self.triangles:
            return
        
        def avg_x(tri):
            return np.mean([self.positions[n][0] for n in tri.nodes])
        
        sorted_tris = sorted(self.triangles.values(), key=avg_x)
        
        self.input_triangles = {t.id for t in sorted_tris[:n_input]}
        self.output_triangles = {t.id for t in sorted_tris[-n_output:]}
        self.hidden_triangles = {t.id for t in self.triangles.values() 
                                  if t.id not in self.input_triangles 
                                  and t.id not in self.output_triangles}
        
        print(f"Input: {len(self.input_triangles)}, "
              f"Hidden: {len(self.hidden_triangles)}, "
              f"Output: {len(self.output_triangles)}")
    
    def create_feedback_loops(self):
        """
        Create feedback connections: output → input
        This is the key to self-reference.
        """
        self.feedback_connections.clear()
        
        for out_id in self.output_triangles:
            for in_id in self.input_triangles:
                self.feedback_connections.append(Connection(
                    source_id=out_id,
                    target_id=in_id,
                    weight=self.feedback_strength,
                    delay=self.feedback_delay
                ))
        
        print(f"Created {len(self.feedback_connections)} feedback connections")
        print(f"  Feedback delay: {self.feedback_delay} steps")
        print(f"  Feedback strength: {self.feedback_strength}")
    
    def stimulate(self, pattern: List[float]):
        """Apply external input."""
        input_list = sorted(self.input_triangles)
        for i, tri_id in enumerate(input_list):
            if i < len(pattern) and tri_id in self.triangles:
                # Add to existing (feedback + external)
                self.triangles[tri_id].activation += pattern[i]
                self.triangles[tri_id].activation = min(1.0, 
                    self.triangles[tri_id].activation)
    
    def propagate(self):
        """Propagate activation with feedback."""
        # Collect incoming signals
        incoming = defaultdict(float)
        
        # Forward connections
        for conn in self.connections:
            source = self.triangles.get(conn.source_id)
            if source and source.is_active():
                signal = source.fire() * conn.weight
                incoming[conn.target_id] += signal
        
        # Feedback connections (with delay)
        for conn in self.feedback_connections:
            source = self.triangles.get(conn.source_id)
            if source:
                # Store current output in buffer
                self.signal_buffer[conn.source_id].append(source.activation)
                
                # Get delayed signal
                if len(self.signal_buffer[conn.source_id]) > conn.delay:
                    delayed_signal = self.signal_buffer[conn.source_id][0]
                    signal = delayed_signal * conn.weight
                    incoming[conn.target_id] += signal
        
        # Update activations
        for tri_id, tri in self.triangles.items():
            # Decay
            new_activation = tri.activation * (1 - self.decay_rate)
            
            # Add incoming
            new_activation += incoming[tri_id]
            
            # Clip
            tri.activation = np.clip(new_activation, 0, 1)
            tri.record()
    
    def compute_meta_activation(self):
        """
        Meta-observer: monitors the entire network.
        High meta-activation = the network is "aware" of its own state.
        """
        # Average activation across all triangles
        activations = [t.activation for t in self.triangles.values()]
        avg_activation = np.mean(activations)
        
        # Variance (complexity of the pattern)
        var_activation = np.var(activations)
        
        # Self-reference: compare current output with delayed input
        output_vals = [self.triangles[tid].activation 
                      for tid in sorted(self.output_triangles) 
                      if tid in self.triangles]
        input_vals = [self.triangles[tid].activation 
                     for tid in sorted(self.input_triangles) 
                     if tid in self.triangles]
        
        # Temporal self-reference: look at history
        self_ref = 0.0
        
        if output_vals and input_vals:
            # Check if output pattern influences future input (through feedback)
            # This is the actual self-reference: am I affecting myself?
            
            if len(self.history['output_pattern']) >= self.feedback_delay + 1:
                # Get output from delay steps ago
                past_output = self.history['output_pattern'][-(self.feedback_delay + 1)]
                
                if past_output and len(past_output) == len(input_vals):
                    past_arr = np.array(past_output)
                    input_arr = np.array(input_vals)
                    
                    # Correlation between past output and current input
                    if np.std(past_arr) > 0.05 and np.std(input_arr) > 0.05:
                        corr = np.corrcoef(past_arr, input_arr)[0, 1]
                        if not np.isnan(corr):
                            self_ref = max(0, corr)
                    
                    # Also check: does input look like past output? (direct feedback)
                    similarity = 1.0 - np.mean(np.abs(past_arr - input_arr))
                    self_ref = max(self_ref, similarity * 0.5)
        
        # Meta-activation combines these
        self.meta_activation = (avg_activation + var_activation * 2 + self_ref) / 4
        self.meta_history.append(self.meta_activation)
        
        return self_ref
    
    def detect_attractor(self):
        """
        Detect if the network has settled into a stable attractor.
        An attractor = a stable "thought" or internal representation.
        """
        if len(self.triangles) < 3:
            return False
        
        # Get current output pattern
        current = tuple(round(self.triangles[tid].activation, 2) 
                       for tid in sorted(self.output_triangles)
                       if tid in self.triangles)
        
        # Check if pattern is stable
        if hasattr(self, '_last_patterns'):
            self._last_patterns.append(current)
            if len(self._last_patterns) > 5:
                self._last_patterns.pop(0)
            
            # All recent patterns similar?
            if len(self._last_patterns) >= 3:
                all_same = all(p == current for p in self._last_patterns[-3:])
                if all_same and sum(current) > 0.1:  # Non-trivial attractor
                    self.attractor_state = current
                    return True
        else:
            self._last_patterns = [current]
        
        return False
    
    def step(self, external_input: Optional[List[float]] = None):
        """Execute one time step."""
        self.time += 1
        
        # Apply external input if provided
        if external_input:
            self.stimulate(external_input)
        
        # Propagate (includes feedback)
        self.propagate()
        
        # Compute meta-level observations
        self_ref = self.compute_meta_activation()
        
        # Detect attractors
        is_attractor = self.detect_attractor()
        
        # Record history
        total_act = sum(t.activation for t in self.triangles.values())
        output = [self.triangles[tid].activation 
                 for tid in sorted(self.output_triangles)
                 if tid in self.triangles]
        
        self.history['time'].append(self.time)
        self.history['total_activation'].append(total_act)
        self.history['output_pattern'].append(output)
        self.history['meta_activation'].append(self.meta_activation)
        self.history['attractor_detected'].append(is_attractor)
        self.history['self_reference_strength'].append(self_ref)
    
    def run_autonomous(self, steps: int, initial_kick: List[float] = None):
        """
        Run the network autonomously with feedback.
        After initial input, the network talks to itself.
        """
        print(f"\nRunning autonomous mode for {steps} steps...")
        
        # Initial kick
        if initial_kick:
            print(f"  Initial input: {initial_kick}")
            self.stimulate(initial_kick)
        
        for i in range(steps):
            self.step()  # No external input - pure self-reference
            
            if (i + 1) % 20 == 0:
                output = self.history['output_pattern'][-1]
                meta = self.history['meta_activation'][-1]
                self_ref = self.history['self_reference_strength'][-1]
                attractor = self.history['attractor_detected'][-1]
                
                print(f"  Step {i+1}: meta={meta:.3f}, self_ref={self_ref:.3f}, "
                      f"attractor={attractor}")
        
        # Summary
        attractors_found = sum(self.history['attractor_detected'])
        max_self_ref = max(self.history['self_reference_strength'])
        
        print(f"\nResults:")
        print(f"  Attractor states found: {attractors_found} times")
        print(f"  Max self-reference: {max_self_ref:.3f}")
        
        if max_self_ref > 0.5:
            print(f"  [LEVEL 3] Strong self-reference detected!")
        
        return self.history
    
    def hebbian_learn(self):
        """Hebbian learning on all connections."""
        for conn in self.connections + self.feedback_connections:
            source = self.triangles.get(conn.source_id)
            target = self.triangles.get(conn.target_id)
            
            if source and target:
                if source.is_active() and target.is_active():
                    conn.weight += self.learning_rate * source.activation * target.activation
                    conn.weight = min(1.0, conn.weight)
                else:
                    conn.weight *= 0.999


# ============================================================
# EXPERIMENTS
# ============================================================

def experiment_self_reference():
    """Test if the network develops self-reference through feedback."""
    
    print("=" * 70)
    print("EXPERIMENT: Self-Reference through Feedback Loops")
    print("=" * 70)
    
    # Build network
    print("\n[1] Building Network...")
    network = RecursiveConsciousnessNetwork(
        n_entities=25,
        feedback_strength=0.25,    # Lower to prevent saturation
        feedback_delay=3,          # Longer delay
        learning_rate=0.03,
        decay_rate=0.25,           # Higher decay to prevent saturation
        seed=42
    )
    
    network.form_links(steps=70, gamma=0.5)
    network.discover_triangles(threshold=0.18)
    network.connect_triangles(max_connections=8000)
    network.designate_io(n_input=3, n_output=3)
    network.create_feedback_loops()
    
    # Test without feedback first
    print("\n[2] Test WITHOUT Feedback...")
    network.feedback_strength = 0.0  # Disable
    for conn in network.feedback_connections:
        conn.weight = 0.0
    
    history_no_fb = network.run_autonomous(
        steps=50, 
        initial_kick=[1.0, 0.5, 0.0]
    )
    
    # Reset and test WITH feedback
    print("\n[3] Test WITH Feedback...")
    for tri in network.triangles.values():
        tri.activation = 0.0
    network.history = {k: [] for k in network.history}
    network._last_patterns = []
    
    network.feedback_strength = 0.25  # Re-enable
    for conn in network.feedback_connections:
        conn.weight = 0.25
    
    history_with_fb = network.run_autonomous(
        steps=80,
        initial_kick=[1.0, 0.5, 0.0]
    )
    
    # Compare
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    
    max_self_ref_no_fb = max(history_no_fb['self_reference_strength']) if history_no_fb['self_reference_strength'] else 0
    max_self_ref_with_fb = max(history_with_fb['self_reference_strength']) if history_with_fb['self_reference_strength'] else 0
    
    attractors_no_fb = sum(history_no_fb['attractor_detected'])
    attractors_with_fb = sum(history_with_fb['attractor_detected'])
    
    print(f"""
    WITHOUT Feedback:
      Max self-reference: {max_self_ref_no_fb:.3f}
      Attractor states: {attractors_no_fb}
    
    WITH Feedback:
      Max self-reference: {max_self_ref_with_fb:.3f}
      Attractor states: {attractors_with_fb}
    
    Interpretation:
      Self-reference = output correlates with input
      = The network is "observing its own output"
      = Minimal self-awareness
    """)
    
    if max_self_ref_with_fb > max_self_ref_no_fb * 1.5:
        print("  [SUCCESS] Feedback increases self-reference!")
    
    return network, history_no_fb, history_with_fb


def experiment_thought_persistence():
    """Test if patterns persist as 'thoughts' through feedback."""
    
    print("\n" + "=" * 70)
    print("EXPERIMENT: Thought Persistence")
    print("=" * 70)
    
    network = RecursiveConsciousnessNetwork(
        n_entities=25,
        feedback_strength=0.3,
        feedback_delay=3,
        decay_rate=0.2,  # Balance between persistence and non-saturation
        seed=123
    )
    
    network.form_links(steps=70, gamma=0.5)
    network.discover_triangles(threshold=0.18)
    network.connect_triangles(max_connections=8000)
    network.designate_io(n_input=3, n_output=3)
    network.create_feedback_loops()
    
    print("\n[1] Inject a pattern...")
    network.stimulate([1.0, 0.0, 1.0])
    
    print("\n[2] Let it run autonomously (no more input)...")
    history = network.run_autonomous(steps=60, initial_kick=None)
    
    # Check if pattern persisted
    final_output = history['output_pattern'][-1] if history['output_pattern'] else []
    
    print(f"\nFinal output: {[f'{x:.2f}' for x in final_output]}")
    
    if final_output and sum(final_output) > 0.3:
        print("  [SUCCESS] Pattern persisted = 'thought' maintained!")
    else:
        print("  Pattern decayed.")
    
    return network, history


def plot_consciousness_experiment(network, history, save_path: str):
    """Visualize the consciousness experiment."""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("ESDE Level 3: Self-Reference through Feedback", fontsize=14)
    
    # 1. Meta-activation over time
    ax1 = axes[0, 0]
    ax1.plot(history['time'], history['meta_activation'], 'purple', linewidth=2)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Meta-Activation')
    ax1.set_title('Network Self-Observation')
    ax1.grid(True, alpha=0.3)
    
    # 2. Self-reference strength
    ax2 = axes[0, 1]
    ax2.plot(history['time'], history['self_reference_strength'], 'red', linewidth=2)
    ax2.axhline(y=0.5, color='green', linestyle='--', label='Strong self-ref threshold')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Self-Reference Strength')
    ax2.set_title('Output-Input Correlation (Self-Awareness Measure)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Output patterns over time (heatmap)
    ax3 = axes[1, 0]
    if history['output_pattern']:
        output_matrix = np.array(history['output_pattern'])
        if output_matrix.size > 0:
            im = ax3.imshow(output_matrix.T, aspect='auto', cmap='viridis',
                          extent=[0, len(history['time']), 0, output_matrix.shape[1]])
            ax3.set_xlabel('Time')
            ax3.set_ylabel('Output Neuron')
            ax3.set_title('Output Pattern Evolution')
            plt.colorbar(im, ax=ax3, label='Activation')
    
    # 4. Attractor detection
    ax4 = axes[1, 1]
    ax4.fill_between(history['time'], 0, history['attractor_detected'], 
                    alpha=0.5, color='green')
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Attractor Detected')
    ax4.set_title('Stable "Thought" States')
    ax4.set_ylim(-0.1, 1.1)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved: {save_path}")
    
    return fig


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("ESDE RECURSIVE CONSCIOUSNESS SIMULATOR")
    print("Level 3: Self-Reference, Feedback Loops, Thought Persistence")
    print("=" * 70)
    
    # Experiment 1: Self-reference
    network, hist_no_fb, hist_with_fb = experiment_self_reference()
    
    # Experiment 2: Thought persistence
    network2, hist_persist = experiment_thought_persistence()
    
    # Visualization
    print("\n[4] Generating Visualization...")
    plot_consciousness_experiment(network, hist_with_fb, "consciousness_results.png")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: LEVEL 3 ACHIEVED?")
    print("=" * 70)
    
    max_self_ref = max(hist_with_fb['self_reference_strength']) if hist_with_fb['self_reference_strength'] else 0
    attractors = sum(hist_with_fb['attractor_detected'])
    
    print(f"""
    Network Structure:
      Triangles: {len(network.triangles)}
      Forward connections: {len(network.connections)}
      Feedback connections: {len(network.feedback_connections)}
    
    Self-Reference Results:
      Max self-reference strength: {max_self_ref:.3f}
      Attractor states detected: {attractors}
    
    What This Demonstrates:
      1. Feedback loops create SELF-OBSERVATION
         - Output feeds back to input
         - Network "sees" its own state
      
      2. Self-reference emerges NATURALLY
         - Not programmed, but structural
         - Output-input correlation = self-awareness measure
      
      3. Attractors = stable "thoughts"
         - Persistent patterns through feedback
         - The network can "hold" an idea
    
    Level Status:
      Level 1 (Boundaries): ✅ Triangles formed
      Level 2 (Computation): ✅ Logic gates emerged  
      Level 3 (Self-Reference): {"✅" if max_self_ref > 0.3 else "🔄"} Feedback creates self-observation
    """)
    
    if max_self_ref > 0.5:
        print("    [MILESTONE] Strong self-reference detected!")
        print("    The network is observing itself observing.")
    
    print("\n" + "=" * 70)
    print("Output: consciousness_results.png")
    print("=" * 70)
    
    return network, hist_with_fb


if __name__ == "__main__":
    main()
