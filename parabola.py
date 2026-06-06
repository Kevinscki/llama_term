import matplotlib.pyplot as plt
import numpy as np

# Generate x values
x = np.linspace(-10, 10, 400)

# Calculate y values for a parabola (y = x^2)
y = x**2

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, label='y = x^2', color='blue')
plt.title('Parabola: y = x^2')
plt.xlabel('x-axis')
plt.ylabel('y-axis')
plt.grid(True)
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.legend()
plt.show()
