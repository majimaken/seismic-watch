import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- STREAMLIT UI SETUP ---
st.title("Plot of a Damped Oscillation")
# Display the mathematical function using LaTeX
st.latex(r"f(x) = e^{-0.1x} \cos(2\pi x)")

# --- MATHEMATICAL FUNCTION ---
def damped_cosine(x):
    # Calculates f(x) = e^(-0.1x) * cos(2*pi*x)
    return np.exp(-0.1 * x) * np.cos(2 * np.pi * x)

# --- SLIDER INPUT ---
x_min, x_max = 0.0, 20.0
# User selects an x-value using a slider
x_val = st.slider(
    "Select an x-value:",
    min_value=x_min,
    max_value=x_max,
    value=5.0,
    step=0.01
)

# --- DATA GENERATION ---
# Generate data points for the entire curve
x_curve = np.linspace(x_min, x_max, 500)
y_curve = damped_cosine(x_curve)

# Calculate the y-value for the selected x
y_val = damped_cosine(x_val)

# --- MATPLOTLIB PLOT ---
# Create a figure and axes for the plot
fig, ax = plt.subplots(figsize=(10, 4))

# Plot the entire curve
ax.plot(x_curve, y_curve, label=r'$f(x)$', color='blue', linewidth=2)

# Highlight the selected point
ax.plot(x_val, y_val, 'ro', markersize=8, label=f'Point at x={x_val:.2f}')

# Add a vertical dashed line at the selected x-value
ax.axvline(x=x_val, color='red', linestyle='--', linewidth=0.8)

# Set labels and add a grid
ax.set_xlabel('x')
ax.set_ylabel('f(x)')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend()

# Display the plot in Streamlit
st.pyplot(fig)

# --- DISPLAY SELECTED VALUE ---
# Display the calculated function value
st.markdown(f"For the selected $\mathbf{{x}}$ of $\mathbf{{{x_val:.2f}}}$, $\mathbf{{f(x)}}$ is equal to: **`{y_val:.4f}`**")