"""
File: blood_modelv3.py
---------------------
This program inputs tiff files of horizontally diffracted light and collapses them
into one dimention. It then outputs a line spectrum as a 1D vector. We combine these vectors
into a dataframe with n rows, where n is the number of files. Each file is labeled by it's
type of red or white blood cells.

The second part of the file is meant to create a logistic regression model that can discriminate
between red and white spectra.

With Pandas
"""

import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
from scipy import signal
from PIL import Image
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import plot_confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn import metrics
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
sns.set (style = "white")
sns.set (style = "whitegrid", color_codes = True)



# Import files here
# FILENAME_RBC_HG = "Basler_acA1300-200um__23253950__20201024_201100038_4.tiff"
# FILENAME_WBC_HG = "Basler_acA1300-200um__23253950__20201024_201302105_4.tiff"
# FILENAME_PAPER_HG = "Basler_acA1300-200um__23253950__20201024_201427690_4.tiff"

DATA_FOLDER_RBC = os.path.join('E:\\', 'Quake', '2020-10-24', 'RBC', 'LED')
DATA_FOLDER_WBC = os.path.join('E:\\', 'Quake', '2020-10-24', 'WBC', 'LED')
DATA_FOLDER_PAPER = os.path.join('E:\\', 'Quake', '2020-10-24', 'PAPER')

# Matplotlib Parameters:
plt.rcParams['figure.figsize'] = (6, 4)
plt.rcParams['figure.dpi'] = 150

# Gain Parameters:
GAIN = 5

"""
This program opens a file and displays it to the user. 
"""
def main():
    # Make arrays
    rbc_array = make_array(DATA_FOLDER_RBC)
    wbc_array = make_array(DATA_FOLDER_WBC)
    # Combine into a large dataframe, add column that classifies
    # red and white blood cells
    df = make_dataframe(rbc_array, wbc_array)
    make_logistic_regression(df)
    # Make a version of the dataframe without labels, for testing the model effectiveness
    df_unlabeled = df.iloc[:, 0:1279]
    # Do k means clustering to see if the data clusters into natural groups (and if they are the correct groups)
    kmeans = KMeans(init = "random",
                    n_clusters = 2,
                    n_init = 10,
                    max_iter = 300,
                    random_state = 0)
    kmeans.fit(df_unlabeled)
    print(kmeans.labels_)
    # Perform PCA to visualize the separation of your data into 2D space.
    pca = PCA(n_components = 2,
              random_state=0)
    pca.fit(df_unlabeled)
    df_scree = make_scree(df_unlabeled)
    fig1, ax1 = plt.subplots()
    ax1.set(yscale="log")
    ax1.set_title("PCA Scree plot", fontsize = 20)
    plt.xlim(1, 24)
    plt.ylim(0.0000001, 1)
    sns.lineplot(x = 'Principal Component', y= "Variance Ratio",
                data = df_scree, ax = ax1)
    plt.show()
    principal_components = pca.fit_transform(df_unlabeled)
    print(principal_components)
    principal_df = pd.DataFrame(data=principal_components,
                                columns=['principal component 1',
                                         'principal component 2'])
    print(principal_df)
    print(df['1280'].tolist())
    # final_df = pd.concat([principal_df, df["1280"]], axis=1)
    principal_df["Color"] = df['1280'].tolist()
    print(principal_df)
    # Works up to here

    # Plot the PCA
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlabel('Principal Component 1', fontsize=15)
    ax.set_ylabel('Principal Component 2', fontsize=15)
    ax.set_title('2 component PCA', fontsize=20)

    targets = [1, 0]
    colors = ['r', 'b']
    for target, color in zip(targets, colors):
        indicesToKeep = principal_df['Color'] == target
        ax.scatter(principal_df.loc[indicesToKeep, 'principal component 1'],
                   principal_df.loc[indicesToKeep, 'principal component 2'],
                   c= color, s= 50)
    ax.legend(targets)
    ax.grid()
    plt.show()



def make_scree(df):
    pca_scree = PCA(n_components=25, random_state = 0)
    pca_scree.fit(df)
    df_new = pd.DataFrame({'Variance Ratio': pca_scree.explained_variance_ratio_,
                       'Principal Component': np.arange(1, pca_scree.n_components_+1)})
    # df_new['var'] = df_new['var'].round(decimals=5)
    return df_new


""" 
This function collapses a folder of 2D image arrays into a 2D array of 1D arrays. 
The 1D arrays are rows in the array.
Inputs: filefolder name
Outputs: 2D numpy array 
"""
def make_array(filefolder):
    # Initialize and create the list of filenames
    file_list = []
    for file in os.listdir(filefolder):
        file_list.append(file)
    # initialize the array
    image1 = cv2.imread(os.path.join(filefolder, file_list[0]), 0)
    print(image1[100])
    mean_spectra1 = np.mean(image1, axis=0)
    # Initialize lists to store arrays
    array_list = []
    array_list_image = []

    # Build arrays
    for file in file_list:
        # Read file
        image = cv2.imread(os.path.join(filefolder, file), 0)
        # Collapse from 2D to 1D by averaging by column.
        mean_spectra = np.mean(image, axis=0)
        mean_spectra = GAIN*mean_spectra
        array_list.append(mean_spectra.round())
        for i in range(30):
            array_list_image.append(mean_spectra.round())
    array = np.stack(array_list)
    array_image = np.stack(array_list_image)
    print(array_image.shape)
    # # Display image of first file (raw)
    # cv2.imshow('lol', image1)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # # Display image of averaged files
    # im = Image.fromarray(array_image)
    # im.show()
    return array

"""
This function takes two numpy array inputs and makes a dataframe, assigning
the value of 1 to red blood cells and 0 to white blood cells. 
Inputs: 2 numpy arrays of same width (column number)
Outputs: dataframe combining the 2 arrays, with one extra column (1 or 0)
"""
def make_dataframe(rbc, wbc):
    # Make first dataframe
    df1 = pd.DataFrame(data = rbc)
    df1.insert(1280, # Column number
               "1280", # Column name
               1, # Value
               True) # Allow repeats?
    # Make second dataframe
    df2 = pd.DataFrame(data= wbc)
    df2.insert(1280,  # Column number
               "1280",  # Column name
               0,  # Value
               True)  # Allow repeats?
    # Combine the two dataframes
    frames = [df1, df2]
    df = pd.concat(frames)
    return df


"""
This function performs a Logistic regression. It requires
1281 length 1D arrays as the rows of the dataframe. 
TODO: generalize to any length. 

Inputs: Dataframe with classification row at row 1280
Outputs: VOID
"""
def make_logistic_regression(df):
    # Split the data into two parts: train and test
    train, test = train_test_split(df,
                                   test_size=0.3,
                                   random_state=0)
    # Specify if we have the x or y variable for each aspect of the split.
    x_train = train.iloc[:, 0:1279]
    y_train = train["1280"]
    x_test = test.iloc[:, 0:1279]
    y_test = test["1280"]
    print(y_train)
    print(x_train)
    # Do the logistic regression.
    log_model = LogisticRegression()
    log_model.fit(x_train, y_train)
    y_pred = log_model.predict(x_test)
    # Check the accuracy of the data
    accuracy = accuracy_score(y_test, y_pred)
    print(accuracy)
    score = log_model.score(x_test, y_test)
    print(score)
    # Show the confusion matrix for the data
    confusion_matrix = metrics.confusion_matrix(y_test, y_pred)
    # disp = plot_confusion_matrix(log_model, y_test, y_pred)
    # plt.figure(figsize=(3, 3))
    # sns.heatmap(confusion_matrix, annot=True, fmt=".3f", linewidths=.5, square=True, cmap='Blues_r');
    # plt.ylabel('Actual color');
    # plt.xlabel('Predicted color');
    # all_sample_title = 'Accuracy Score: {0}'.format(score)
    # plt.title("Logistic Regression Confusion Matrix", size=15)
    return 0


if __name__ == '__main__':
    main()
