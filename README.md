# Solution for the gelsight_lab assignment

run `../demos/mini_tracking_linux_V0/tracking_answers.py`

### Shear force visualization
![](demos/mini_tracking_linux_V0/results/shear_flow.gif)

### Twist force visualization
![](demos/mini_tracking_linux_V0/results/twist_flow.gif)

### Operation Demonstration
![](demo1.png)


### Calculating Real-World Displacement from Gelsight Image Movement

To calculate how much a point on the image moves in real-world terms when it shifts by 10 pixels, we need to understand the relationship between the image's pixel dimensions and the real-world dimensions (Field of View).

**Given:**

- **Image Width (imgw):** 320 pixels
- **Image Height (imgh):** 240 pixels
- **Field of View (FOV):** 18.6 mm (Horizontal) x 14.3 mm (Vertical)
- **Movement:** 10 pixels

**Steps:**

1. **Calculate the real-world size of one pixel:**
   - **Horizontal size per pixel:**      

\[
     \text{Horizontal size per pixel} = \frac{18.6 \text{ mm}}{320 \text{ pixels}} = 0.058125 \text{ mm/pixel}
     \]
   - **Vertical size per pixel:**      

\[
     \text{Vertical size per pixel} = \frac{14.3 \text{ mm}}{240 \text{ pixels}} = 0.059583 \text{ mm/pixel}
     \]

2. **Calculate the real-world movement for 10 pixels:**
   - **Horizontal movement:**      

\[
     \text{Horizontal movement} = 10 \text{ pixels} \times 0.058125 \text{ mm/pixel} = 0.58125 \text{ mm}
     \]
   - **Vertical movement:**      

\[
     \text{Vertical movement} = 10 \text{ pixels} \times 0.059583 \text{ mm/pixel} = 0.59583 \text{ mm}
     \]

So, when a point on the image moves 10 pixels, it moves approximately **0.58125 mm horizontally** and **0.59583 mm vertically** in the real world.

### Shear Force Estimation Method

The **Simplified Shear Force Estimation Method** calculates the force exerted on the skin when it undergoes a displacement. By considering the displacement, the thickness of the skin, and the shear modulus (a material property of the skin), this method estimates the resulting shear force.

- **Shear Strain (\(\gamma\))**: Shear strain is defined as the displacement per unit thickness of the skin layer:  

\[
  \gamma = \frac{\text{Displacement}}{\text{Thickness of skin layer}} = \frac{\Delta x}{d}
  \]
  where:
  - \(\Delta x\) is the displacement (in mm),
  - \(d\) is the thickness of the skin layer (in mm).

- **Shear Stress (\(\tau\))**: Shear stress is related to shear strain using the shear modulus \(G\) (a material property of the skin):  

\[
  \tau = G \cdot \gamma = G \cdot \frac{\Delta x}{d}
  \]
  where \(G\) is the shear modulus (in Pa).

- **Shear Force (\(F\))**: Shear force is obtained by multiplying the shear stress by the contact area \(A\):  

\[
  F = \tau \cdot A = G \cdot \frac{\Delta x}{d} \cdot A
  \]
  where \(A\) is the contact area (in m²).

### Twist Force Estimation Method

The **Simplified Twist Force Estimation Method** estimates the force due to a twisting or rotational displacement on the skin. This method is based on the concept of torsional strain and torque.

- **Torsional Strain (\(\gamma_t\))**: Torsional strain is defined as the angular displacement per unit radius of the skin layer:  

\[
  \gamma_t = \frac{\theta}{r}
  \]
  where:
  - \(\theta\) is the angular displacement (in radians),
  - \(r\) is the radius of the area being twisted (in meters).

- **Torsional Stress (\(\tau_t\))**: Torsional stress is related to torsional strain using the torsional shear modulus \(G_t\):  

\[
  \tau_t = G_t \cdot \gamma_t = G_t \cdot \frac{\theta}{r}
  \]
  where \(G_t\) is the torsional shear modulus (in Pa).

- **Torque (\(T\))**: Torque, or twist force, is calculated by multiplying the torsional stress by the moment of area \(J\) (related to the geometry of the skin area being twisted):  

\[
  T = \tau_t \cdot J = G_t \cdot \frac{\theta}{r} \cdot J
  \]
  where \(J\) is the polar moment of inertia (in m⁴), which depends on the geometry of the twisted area.

These simplified methods offer a foundational approach for estimating the mechanical interactions between the skin and external forces, providing a basis for further refinement in experimental or more complex scenarios.


