
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# --- Configuración ---
N_BODIES = 5
STEPS = 300
DT = 0.05
G = 1.0
SOFTENING = 0.1
TRAIL_LEN = 50
OUTPUT_FILE = 'n_body_simulation.mp4'
FPS = 30

# --- Inicialización ---
np.random.seed(42)
masses = np.random.uniform(1.0, 5.0, N_BODIES)
positions = np.random.uniform(-5, 5, (N_BODIES, 3))
velocities = np.random.uniform(-1, 1, (N_BODIES, 3))

# Historial de posiciones
history = np.zeros((STEPS, N_BODIES, 3))

def get_accelerations(pos, masses):
    """Calcula aceleraciones gravitacionales vectorizado."""
    n = len(masses)
    acc = np.zeros((n, 3))
    for i in range(n):
        diff = pos - pos[i]
        dist_sq = np.sum(diff**2, axis=1) + SOFTENING**2
        dist_sqrt = np.sqrt(dist_sq)
        # Evitar división por cero con softening
        acc[i] = np.sum((G * masses[:, None] * diff / dist_sqrt[:, None]) / dist_sq[:, None], axis=0)
    return acc

def simulate():
    """Ejecuta la integración de Verlet y guarda historial."""
    global positions, velocities
    acc = get_accelerations(positions, masses)
    
    for i in range(STEPS):
        # Verlet Step
        pos_new = positions + velocities * DT + 0.5 * acc * DT**2
        acc_new = get_accelerations(pos_new, masses)
        velocities = velocities + 0.5 * (acc + acc_new) * DT
        positions = pos_new
        acc = acc_new
        history[i] = positions

def update(frame):
    """Actualiza la animación."""
    ax.clear()
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_zlim(-10, 10)
    ax.set_title(f"N-Body Simulation (Verlet) - Step {frame}/{STEPS}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    
    # Dibujar estelas y cuerpos
    for i in range(N_BODIES):
        start_idx = max(0, frame - TRAIL_LEN)
        trail = history[start_idx:frame+1, i, :]
        if len(trail) > 1:
            ax.plot(trail[:, 0], trail[:, 1], trail[:, 2], alpha=0.4, linewidth=1.5)
        
        ax.scatter(history[frame, i, 0], history[frame, i, 1], history[frame, i, 2], 
                   s=masses[i]*10, color=plt.cm.viridis(i/N_BODIES), depthshade=True)

if __name__ == "__main__":
    print("Iniciando simulación...")
    simulate()
    
    print("Generando animación...")
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    anim = FuncAnimation(fig, update, frames=STEPS, interval=20)
    
    print(f"Guardando video en: {OUTPUT_FILE}")
    anim.save(OUTPUT_FILE, writer='ffmpeg', fps=FPS)
    plt.close()
    print("Completado.")
