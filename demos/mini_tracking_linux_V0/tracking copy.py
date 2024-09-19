import copy
import find_marker
import numpy as np
import cv2
import time
import marker_detection
import sys
import setting
import os

def find_cameras():
    # checks the first 10 indexes.
    index = 0
    arr = []
    if os.name == 'nt':
        cameras = find_cameras_windows()
        return cameras
    i = 10
    while i >= 0:
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            command = 'v4l2-ctl -d ' + str(index) + ' --info'
            is_arducam = os.popen(command).read()
            if is_arducam.find('Arducam') != -1 or is_arducam.find('Mini') != -1:
                arr.append(index)
            cap.release()
        index += 1
        i -= 1

    return arr

def find_cameras_windows():
    # checks the first 10 indexes.
    index = 0
    arr = []
    idVendor = 0xC45
    idProduct = 0x636D
    import usb.core
    import usb.backend.libusb1
    backend = usb.backend.libusb1.get_backend(
        find_library=lambda x: "libusb_win/libusb-1.0.dll"
    )
    dev = usb.core.find(backend=backend, find_all=True)
    # loop through devices, printing vendor and product ids in decimal and hex
    for cfg in dev:
        #print('Decimal VendorID=' + hex(cfg.idVendor) + ' & ProductID=' + hex(cfg.idProduct) + '\n')
        if cfg.idVendor == idVendor and cfg.idProduct == idProduct:
            arr.append(index)
        index += 1

    return arr


def resize_crop_mini(img, imgw, imgh):
    # resize, crop and resize back
    img = cv2.resize(img, (895, 672))  # size suggested by janos to maintain aspect ratio
    border_size_x, border_size_y = int(img.shape[0] * (1 / 7)), int(np.floor(img.shape[1] * (1 / 7)))  # remove 1/7th of border from each size
    img = img[border_size_x:img.shape[0] - border_size_x, border_size_y:img.shape[1] - border_size_y]
    img = img[:, :-1]  # remove last column to get a popular image resolution
    img = cv2.resize(img, (imgw, imgh))  # final resize for 3d
    return img

def trim(img):
    img[img<0] = 0
    img[img>255] = 255



def compute_tracker_gel_stats(thresh):
    numcircles = 9 * 7;
    mmpp = .063;
    true_radius_mm = .5;
    true_radius_pixels = true_radius_mm / mmpp;
    circles = np.where(thresh)[0].shape[0]
    circlearea = circles / numcircles;
    radius = np.sqrt(circlearea / np.pi);
    radius_in_mm = radius * mmpp;
    percent_coverage = circlearea / (np.pi * (true_radius_pixels) ** 2);
    return radius_in_mm, percent_coverage*100.


def calculate_mean_phase_difference(Ox, Oy, Cx, Cy):
    # Convert lists to numpy arrays
    Ox = np.array(Ox)
    Oy = np.array(Oy)
    Cx = np.array(Cx)
    Cy = np.array(Cy)

    # Calculate phase differences for each marker
    phase_differences = np.arctan2(Cy - Oy, Cx - Ox)
    
    # Calculate the mean of all phase differences
    mean_phase_difference = np.mean(phase_differences)
    
    return mean_phase_difference

def main(argv):
    imgw = 320
    imgh = 240
    calibrate = False
    outdir = './TEST/'
    SAVE_VIDEO_FLAG = False
    SAVE_ONE_IMG_FLAG = False
    SAVE_DATA_FLAG = False

    cameras = find_cameras()
    cap = cv2.VideoCapture(cameras[0])
    WHILE_COND = cap.isOpened()
    cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc('M','J','P','G'))
    setting.init()

    frame0 = None
    counter = 0
    while 1:
        if counter < 50:
            ret, frame = cap.read()
            if counter == 48:
                ret, frame = cap.read()
                frame = resize_crop_mini(frame, imgw, imgh)
                mask = marker_detection.find_marker(frame)
                mc = marker_detection.marker_center(mask, frame)
                break
            counter += 1

    counter = 0
    mccopy = mc
    mc_sorted1 = mc[mc[:, 0].argsort()]
    mc1 = mc_sorted1[:setting.N_]
    mc1 = mc1[mc1[:, 1].argsort()]

    mc_sorted2 = mc[mc[:, 1].argsort()]
    mc2 = mc_sorted2[:setting.M_]
    mc2 = mc2[mc2[:, 0].argsort()]

    N_ = setting.N_
    M_ = setting.M_
    fps_ = setting.fps_
    x0_ = np.round(mc1[0][0])
    y0_ = np.round(mc1[0][1])
    dx_ = mc2[1, 0] - mc2[0, 0]
    dy_ = mc1[1, 1] - mc1[0, 1]

    print('x0:', x0_, '\n', 'y0:', y0_, '\n', 'dx:', dx_, '\n', 'dy:', dy_)

    radius, coverage = compute_tracker_gel_stats(mask)
    m = find_marker.Matching(N_, M_, fps_, x0_, y0_, dx_, dy_)

    frameno = 0
    try:
        while (WHILE_COND):
            ret, frame = cap.read()
            if not ret:
                break

            frame = resize_crop_mini(frame, imgw, imgh)
            raw_img = copy.deepcopy(frame)
            mask = marker_detection.find_marker(frame)
            mc = marker_detection.marker_center(mask, frame)

            if not calibrate:
                tm = time.time()
                m.init(mc)
                m.run()

                flow = m.get_flow()
                Ox, Oy, Cx, Cy, Occupied = flow

                # Calculate the mean phase difference
                mean_phase_diff = calculate_mean_phase_difference(Ox, Oy, Cx, Cy)
                print(f"Mean Phase Difference: {mean_phase_diff:.4f} radians")

                frameno += 1

    except KeyboardInterrupt:
        print('Interrupted!')

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main(sys.argv[1:])
