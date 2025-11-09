import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
x_min, x_max = 0.0, 20.0
# Using simplified function names for better UX
DEFAULT_FUNCTION = "exp(-0.1 * x) * cos(2 * pi * x)"

# --- HELPER FUNCTION: FUNCTION EXECUTION LOGIC (SIMPLIFIED) ---
def evaluate_user_function(x, function_str):
    """
    Safely evaluates the user-provided function string, 
    exposing common math functions directly for ease of use.
    """
    safe_dict = {
        'x': x,
        # Expose common NumPy math functions without the 'np.' prefix
        'exp': np.exp,
        'cos': np.cos,
        'sin': np.sin,
        'log': np.log,
        'sqrt': np.sqrt,
        'pi': np.pi,
        'power': np.power
    }
    try:
        return eval(function_str, {"__builtins__": {}}, safe_dict)
    except Exception as e:
        st.session_state['error'] = True
        st.error(f"Error evaluating function: **{e}**")
        return np.zeros_like(x)

# --- STREAMLIT UI SETUP ---
st.set_page_config(layout="wide") # Use wide layout
st.title("Function Plotter")
st.markdown("---")

# Initialize error state
if 'error' not in st.session_state:
    st.session_state['error'] = False
st.session_state['error'] = False

# --- COLUMN LAYOUT FOR INPUTS ---
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Define Your Own Function $f(x)$")
    user_function_str = st.text_input(
        "Enter function:",
        value=DEFAULT_FUNCTION,
        key="function_input"
    )

with col2:
    st.subheader("Select $x$ Value")
    x_val = st.slider(
        "x value for point highlight:",
        min_value=x_min,
        max_value=x_max,
        value=5.0,
        step=0.01
    )

st.markdown(f"**Current Function:** $f(x) = {user_function_str}$")

# --- EXPANDER FOR GUIDANCE ---
with st.expander("Available Math Functions"):
    st.markdown("""
        Use **`x`** as the variable. Available functions and constants are:
        * **`exp(x)`**: $e^x$
        * **`cos(x)`**, **`sin(x)`**: Trigonometric functions (in radians)
        * **`log(x)`**: Natural logarithm ($\ln(x)$)
        * **`sqrt(x)`**: Square root ($\sqrt{x}$)
        * **`power(x, y)`**: $x^y$
        * **`pi`**: The constant $\pi$
        """)
st.markdown("---")


# --- DATA GENERATION ---
x_curve = np.linspace(x_min, x_max, 500)
y_curve = evaluate_user_function(x_curve, user_function_str)

# Only proceed with plot/value calculation if no error occurred
if not st.session_state['error']:
    y_val_array = evaluate_user_function(np.array([x_val]), user_function_str)
    y_val = y_val_array[0] if y_val_array.size > 0 else 0.0

    # --- DISPLAY SELECTED VALUE ---
    st.markdown(f"For the selected $\mathbf{{x}}$ of $\mathbf{{{x_val:.2f}}}$, $\mathbf{{f(x)}}$ is equal to: **`{y_val:.4f}`**")

    # --- MATPLOTLIB PLOT ---
    fig, ax = plt.subplots(figsize=(10, 3.5)) 
    ax.plot(x_curve, y_curve, label=r'$f(x)$', color='blue', linewidth=2)
    ax.plot(x_val, y_val, 'ro', markersize=8, label=f'Point at x={x_val:.2f}')
    ax.axvline(x=x_val, color='red', linestyle='--', linewidth=0.8)
    ax.set_xlabel('x')
    ax.set_ylabel('f(x)')
    ax.set_title("Plot of the Function")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    st.pyplot(fig)

    # --- DISPLAY SELECTED VALUE ---
    st.markdown(f"For the selected $\mathbf{{x}}$ of $\mathbf{{{x_val:.2f}}}$, $\mathbf{{f(x)}}$ is equal to: **`{y_val:.4f}`**")