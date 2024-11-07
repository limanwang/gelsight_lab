import sys
import numpy as np
import cv2
import os
import gsdevice
import gs3drecon

def draw_optical_flow(img, flow, step=16, scale=5, thickness=2, tip_length=0.5):
    """
    Function to draw the optical flow vectors on the image.

    Args:
        img: The image on which to draw.
        flow: The optical flow array.
        step: The step size for sampling points in the grid.
        scale: Scaling factor to increase the length of the arrows.
        thickness: The thickness of the arrow lines.
        tip_length: The relative size of the arrow tip.
    """
    h, w = img.shape[:2]
    y, x = np.mgrid[step//2:h:step, step//2:w:step].reshape(2, -1).astype(int)
    fx, fy = flow[y, x].T

    # Scale the flow vectors to make the arrows longer
    fx, fy = fx * scale, fy * scale

    # Create line endings for the flow vectors
    lines = np.vstack([x, y, x + fx, y + fy]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)

    # Convert the grayscale image to a BGR image for visualization
    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Draw the flow vectors
    for (x1, y1), (x2, y2) in lines:
        cv2.arrowedLine(vis, (x1, y1), (x2, y2), (0, 255, 0), thickness, tipLength=tip_length)

    return vis

def calculate_real_world_displacement(pixels_x, pixels_y, imgw=320, imgh=240, fov_horizontal=18.6, fov_vertical=14.3):
    """Calculate the real-world displacement in mm for given pixel movements in x and y directions."""
    # Calculate size per pixel in mm
    horizontal_mm_per_pixel = fov_horizontal / imgw
    vertical_mm_per_pixel = fov_vertical / imgh

    # Calculate the real-world movement for the given pixels
    horizontal_movement = pixels_x * horizontal_mm_per_pixel
    vertical_movement = pixels_y * vertical_mm_per_pixel

    return horizontal_movement, vertical_movement

def calculate_shear_force(displacement, skin_thickness=2.0, shear_modulus=7000, contact_area=0.0001):
    """Calculate the shear force based on displacement."""
    # Calculate shear strain
    shear_strain = displacement / skin_thickness

    # Calculate shear stress
    shear_stress = shear_modulus * shear_strain

    # Calculate shear force
    shear_force = shear_stress * contact_area

    return shear_force

def calculate_twist_force(pixels, radius=0.01, torsional_modulus=7000, polar_moment_inertia=1.57e-9):
    """Calculate the twist force based on angular displacement."""
    # Convert pixel displacement to angular displacement (radians)
    theta = np.deg2rad(pixels * (360 / (2 * np.pi * radius * 1000)))  # Convert to radians

    # Calculate torsional strain
    torsional_strain = theta / radius

    # Calculate torsional stress
    torsional_stress = torsional_modulus * torsional_strain

    # Calculate torque
    torque = torsional_stress * polar_moment_inertia

    return torque

def main(argv):
    # Set flags
    SAVE_VIDEO_FLAG = False
    FIND_ROI = False
    GPU = False
    MASK_MARKERS_FLAG = False

    # Path to 3d model
    path = '.'

    # Set the camera resolution
    mmpp = 0.0634  # mini gel 18x24mm at 240x320

    # the device ID can change after unplugging and changing the usb ports.
    dev = gsdevice.Camera("GelSight Mini")
    net_file_path = 'nnmini.pt'

    dev.connect()

    ''' Load neural network '''
    model_file_path = path
    net_path = os.path.join(model_file_path, net_file_path)
    print('net path = ', net_path)

    if GPU:
        gpuorcpu = "cuda"
    else:
        gpuorcpu = "cpu"

    nn = gs3drecon.Reconstruction3D(dev)
    net = nn.load_nn(net_path, gpuorcpu)  # Corrected line

    f1 = dev.get_image()
    prev_gray = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)

    try:
        while dev.while_condition:
            # Get the next frame
            f1 = dev.get_image()

            # Convert the new frame to grayscale
            gray = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)

            # Initialize previous frame if None
            # if prev_gray is None:
            #     prev_gray = gray
            #     continue

            # Compute the optical flow using Farneback's method
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)

            # Separate the x and y components of the flow
            flow_x = flow[..., 0]
            flow_y = flow[..., 1]

            # Calculate the magnitude of the flow vectors (pixel displacement)
            flow_magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
            average_pixel_displacement = np.mean(flow_magnitude)

            # Calculate the average pixel displacement in x and y directions
            average_pixel_displacement_x = np.mean(flow_x)
            average_pixel_displacement_y = np.mean(flow_y)

            # Calculate real-world displacement based on average pixel displacement in x and y
            real_world_displacement_x, real_world_displacement_y = calculate_real_world_displacement(
                average_pixel_displacement_x, average_pixel_displacement_y
            )

            # Calculate shear force based on real-world displacement in x and y directions
            shear_force_x = calculate_shear_force(real_world_displacement_x)
            shear_force_y = calculate_shear_force(real_world_displacement_y)

            # Calculate twist force separately for x and y displacements
            twist_force_x = calculate_twist_force(average_pixel_displacement_x)
            twist_force_y = calculate_twist_force(average_pixel_displacement_y)

            # Calculate twist force based on average pixel displacement
            twist_force = calculate_twist_force(average_pixel_displacement)

            # Print calculated values
            print(f"Average Pixel Displacement X: {average_pixel_displacement_x:.2f} pixels")
            print(f"Average Pixel Displacement Y: {average_pixel_displacement_y:.2f} pixels")
            print(f"Real-World Displacement (mm): Horizontal={real_world_displacement_x:.5f}, Vertical={real_world_displacement_y:.5f}")
            print(f"Shear Force (N): X={shear_force_x:.5e}, Y={shear_force_y:.5e}")
            # print(f"Twist Force (Nm): X={twist_force_x:.5e}, Y={twist_force_y:.5e}")
            print(f"Twist Force (Nm): total={twist_force:.5e}")


            # Draw the optical flow vectors
            flow_image = draw_optical_flow(gray, flow, step=32, scale=5, thickness=2, tip_length=0.3)

            # Display the optical flow result
            bigframe = cv2.resize(flow_image, (flow_image.shape[1] * 2, flow_image.shape[0] * 2))
            cv2.imshow('Optical Flow', bigframe)

            # Check if the user wants to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if SAVE_VIDEO_FLAG:
                out.write(f1)

            # Update previous frame
            # prev_gray = gray

    except KeyboardInterrupt:
        print('Interrupted!')
        dev.stop_video()

if __name__ == "__main__":
    main(sys.argv[1:])
