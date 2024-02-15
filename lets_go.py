import pandas as pd
import rasterio
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from rasterio.plot import show
import os
import warnings
import time
import glob

# Suppress RuntimeWarnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Global variables
current_mode = 'label'  # can be 'add' or 'label'
selected_detection = None
new_detections = []
selection_threshold = 500  # Threshold distance for selecting a detection
press_x, press_y = None, None  # Global variables for mouse press coordinates

def clear_console():
    # Clear the console. Works on Windows (os.system('cls')) and Unix (os.system('clear'))
    os.system('cls' if os.name == 'nt' else 'clear')

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
            new_detections.append({'chipName': image,'x': release_x, 'y': release_y, 'class': 'new_detection'})
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
                plt.title(f'{image} - {closest_detection}', fontsize=10)
                ax.set_xlabel(f'{current_mode} mode. Labeling index: {closest_detection}')
                print(f"Selected detection at index: {closest_detection}")
# Function to handle key press events
def onkey(event, df, image_name, src, fig, ax):
    global current_mode, selected_detection

    # Handle exit first, regardless of other conditions
    if event.key == 'e':
        print("Exiting the program.")
        plt.close(fig)  # Close the plot window
        plt.close('all')  # Close all other plot windows
        raise SystemExit  # Exit the program

    # Then handle other keys based on modes
    if event.key == 'a':
        if current_mode != 'add':  # Only redraw if mode changes
            current_mode = 'add'
            print("Switched to ADD mode. Click to add new detections.")
            draw_plot(image_name, df, src, fig, ax)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel(f'{current_mode} mode')
            plt.title(f'{image_name}', fontsize=10)
    elif event.key == 'l':
        if current_mode != 'label':  # Only redraw if mode changes
            current_mode = 'label'
            print("Switched to LABEL mode. Click to select a detection for labeling.")
            draw_plot(image_name, df, src, fig, ax)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel(f'{current_mode} mode')
            plt.title(f'{image_name}', fontsize=10)
    elif event.key == 'r':
        print("Resetting the image with different colors for labeled detections.")
        draw_plot(image_name, df, src, fig, ax, reset=True)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel(f'{current_mode} mode')
        plt.title(f'{image_name}', fontsize=10)
    elif current_mode == 'label' and selected_detection is not None:
        if event.key in ['m', 'b']:
            status = 'misclassified' if event.key == 'm' else 'bad'
            df.at[selected_detection, 'verification'] = status
            print(f"Labeled detection {selected_detection} as {status}")

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

database = 'wdr_2019_DetectionTable.csv'
# Load the CSV file
df = pd.read_csv(database)

# Load in file with images that have been processed
if os.path.exists('processed.csv'):
    processed_df = pd.read_csv('processed.csv')
    processed_images = processed_df['imgName'].to_list()
    print(f'Total images processed so far: {len(processed_images)}')
else:
    processed_images = []

# Filter rows where class is not 'none'
boats_df = df[df['class'] != 'none']

# New column for verification status
df['verification'] = None

# Assuming your TIFF files are in the same directory
tif_files = glob.glob('**/*.tif',recursive=True)

for i, image_path in enumerate(tif_files):
    clear_console()  # Clear the console
    # Print all messages in the desired order
    print(f"{time.ctime()}")
    print(f"Working on image {i + 1} of {len(tif_files)}")  # Replace 10 with len(tif_files)
    image = os.path.basename(image_path).strip('.tif')

    if image in processed_images or not os.path.exists(image_path):
        continue

    print(f'Current image: {image_path}')
    print("To exit, press e")

    # Open the image using rasterio
    with rasterio.open(image_path) as src:
        fig, ax = plt.subplots(1,figsize=(12,8))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel(f'{current_mode} mode')

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
        # Add text on the right side of the plot within the figure
        info_text = (f'Boats: {bcounts["boat"]}\n'
                     f'Wakes: {bcounts["boat_wake"]}\n\n')
        usage =     (f'r: Reset\n'
                     f'a: Add\n'
                     f'l: Label\n'
                     f'- m: miscls\n'
                     f'- b: bad\n'
                     f'e: exit\n\n')
        misc =      (f'{time.ctime()}\n'
                     f'processing {i + 1} of {len(tif_files)}')

        # Position of the text in figure coordinates (x, y)
        # Adjust these values as needed
        fig.text(0.85, 0.85, info_text, fontsize=9, 
                verticalalignment='center', horizontalalignment='left')
        fig.text(0.85, 0.5, usage, fontsize=8, 
                verticalalignment='center', horizontalalignment='left')
        fig.text(0.85, 0.15, misc, fontsize=8, 
                verticalalignment='center', horizontalalignment='left')
        # ax.xaxis.set_visible(False)
        # ax.yaxis.set_visible(False)
        plt.title(f'{image}', fontsize=10)
        plt.show()

        # Append new detections to the DataFrame
        new_detections_df = pd.DataFrame(new_detections)
        df = pd.concat([df, new_detections_df], ignore_index=True)

        # Add file name to processed file list
        processed_images.append(image)
        p_df = pd.DataFrame({'imgName': processed_images})
        print(f"Saving the updated processed file list to processed.csv")
        p_df.to_csv('processed.csv',index = False)

        # Save updated DataFrame to CSV
        print(f"Saving the updated DataFrame to {database}")
        df.to_csv(database, index=False)

print("All images processed.")
print("Exiting the program.")
