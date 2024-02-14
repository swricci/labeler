import pandas as pd
import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
import os
import warnings
import glob

# Suppress RuntimeWarnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Global variables
current_mode = 'label'  # can be 'add' or 'label'
selected_detection = None
new_detections = []
selection_threshold = 500  # Threshold distance for selecting a detection
press_x, press_y = None, None  # Global variables for mouse press coordinates

# Function to handle mouse press event
def onpress(event):
    global press_x, press_y
    if event.xdata is not None and event.ydata is not None:
        press_x, press_y = event.xdata, event.ydata

# Function to handle mouse release events
def onrelease(event, src, df, fig, ax):
    global current_mode, selected_detection, press_x, press_y
    if event.xdata is None or event.ydata is None:  # Clicked outside the axes
        return
    
    if event.dblclick or event.button != 1:  # Ignore double clicks and non-left clicks
        return
    
    release_x, release_y = event.xdata, event.ydata
    # Check if the mouse was clicked and released at the same position (or very close)
    if press_x is not None and release_x is not None and \
       abs(press_x - release_x) < 5 and abs(press_y - release_y) < 5:
        if current_mode == 'add':
            # Adding new detection
            new_detections.append({'x': release_x, 'y': release_y, 'class': 'new_detection'})
            ax.plot(release_x, release_y, 'go')  # green circle for new detections
            plt.draw()
        elif current_mode == 'label':
            # Labeling existing detection
            closest_detection = None
            min_dist = float('inf')
            for index, row in df.iterrows():
                dist = ((row['x'] - release_x) ** 2 + (row['y'] - release_y) ** 2) ** 0.5
                if dist < min_dist and dist < selection_threshold:
                    min_dist = dist
                    closest_detection = index
            if closest_detection is not None:
                selected_detection = closest_detection
                print(f"Selected detection at index: {closest_detection}")

# Function to handle key press events
def onkey(event, df, image_name, src, fig, ax):
    global current_mode, selected_detection
    if event.key == 'a':
        if current_mode != 'add':  # Only redraw if mode changes
            current_mode = 'add'
            print("Switched to ADD mode. Click to add new detections.")
            draw_plot(image_name, df, src, fig, ax)
    elif event.key == 'l':
        if current_mode != 'label':  # Only redraw if mode changes
            current_mode = 'label'
            print("Switched to LABEL mode. Click to select a detection for labeling.")
            draw_plot(image_name, df, src, fig, ax)
    elif event.key == 'r':
        print("Resetting the image with different colors for labeled detections.")
        draw_plot(image_name, df, src, fig, ax, reset=True)
    elif current_mode == 'label' and selected_detection is not None:
        if event.key in ['m', 'b']:
            status = 'misclassified' if event.key == 'g' else 'bad'
            df.at[selected_detection, 'verification'] = status
            print(f"Labeled detection {selected_detection} as {status}")
            selected_detection = None  # Reset selected detection

# Function to draw the plot
def draw_plot(image_name, df, src, fig, ax, reset=False):
    ax.clear()  # Clear the current axes
    show(src, ax=ax)  # Show the image again
    
    # Place markers for existing detections
    for index, row in df[df['chipName'].str.startswith(image_name)].iterrows():
        if not pd.isna(row['x']) and not pd.isna(row['y']):
            if row['verification'] is not None:
                marker_color = 'green' if row['verification'] == 'misclassified' else 'cyan' if row['verification'] == 'bad' else 'blue'
                marker_style = 'o' if row['verification'] == 'misclassified' or row['verification'] == 'bad' else '+'
                ax.plot(row['x'], row['y'], marker=marker_style, color=marker_color, markersize=15, markeredgewidth=1.5, fillstyle='none')
                ax.plot(row['x'], row['y'], marker='*', color='black', markersize=10)
            else:
                marker = 'ro' if row['class'] == 'boat' else 'b+'
                ax.plot(row['x'], row['y'], marker, markersize=15, markeredgewidth=1.5, fillstyle='none')
    
    # Plot new detections if not resetting
    for detection in new_detections:
        plt.plot(detection['x'], detection['y'], 'go')  # green circle for new detections
    
    plt.draw()  # Redraw the plot

# Load the CSV file
df = pd.read_csv('wdr_2019_DetectionTable.csv')

# Load in file with images that have been processed
processed_df = pd.read_csv('processed.csv')
processed_images = processed_df['imgName'].to_list()
print(processed_images)

# Filter rows where class is not 'none'
boats_df = df[df['class'] != 'none']

# New column for verification status
df['verification'] = None

# Assuming your TIFF files are in the same directory
tif_files = glob.glob('**/*.tif',recursive=True)

for image_path in tif_files:
    # print(image_path)
    image = os.path.basename(image_path).strip('.tif')

    if image in processed_images or not os.path.exists(image_path):
        continue
    
    # Open the image using rasterio
    with rasterio.open(image_path) as src:
        fig, ax = plt.subplots(1)

        # Set the aspect of the plot to be equal and define the limits
        ax.set_aspect('equal')
        ax.set_xlim(src.bounds.left, src.bounds.right)
        ax.set_ylim(src.bounds.bottom, src.bounds.top)

        show(src, ax=ax)

        # Connect mouse press, release, and key press events
        fig.canvas.mpl_connect('button_press_event', onpress)
        fig.canvas.mpl_connect('button_release_event', lambda event: onrelease(event, src, df, fig, ax))
        fig.canvas.mpl_connect('key_press_event', lambda event: onkey(event, df, image, src, fig, ax))

        # Place markers for existing detections
        for index, row in df[df['chipName'].str.startswith(image)].iterrows():
            if not pd.isna(row['x']) and not pd.isna(row['y']):
                marker = 'ro' if row['class'] == 'boat' else 'b+'
                ax.plot(row['x'], row['y'], marker, markersize=15, markeredgewidth=1.5, fillstyle='none')
        
        bcounts = df[df["chipName"].str.startswith(image)]['class'].value_counts()
        plt.title(f'Image {image}, boats: {bcounts['boat']}, wakes: {bcounts['boat_wake']}')
        plt.show()

    # Append new detections to the DataFrame
    new_detections['chipName'] = image
    new_detections_df = pd.DataFrame(new_detections)
    df = pd.concat([df, new_detections_df], ignore_index=True)

    # Add file name to processed file list
    processed_images.append(image)
    p_df = pd.DataFrame({'imgName': processed_images})
    p_df.to_csv('processed.csv',index = False)

    # Save updated DataFrame to CSV
    df.to_csv('updated_wdr_2019_DetectionTable.csv', index=False)

