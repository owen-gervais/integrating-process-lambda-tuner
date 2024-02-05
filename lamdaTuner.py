import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFrame, QWidget, QMenu, QMenuBar, QAction, QWidget, QLabel, QFileDialog, QInputDialog, QMessageBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
import numpy as np

class LambdaTuner(QMainWindow):
    def __init__(self):
        super().__init__()

        # App data
        self.lines = []
        self.pv_x_data = []
        self.pv_y_data = []
        self.cv_x_data = []
        self.cv_y_data = []
        self.slope1 = 0
        self.slope2 = 0
        self.td = 0
        self.delOutput = 0
        self.pvTransPt = 0
        self.cvTransPt = 0
        self.lambdaVal = 0
        self.processGain = 0
        self.proportionalGain = 0
        self.integralTime = 0

        self.locked = True
        self.dataLoaded = False

        # Empty dictionary of labels
        self.labels = {}
        self.init_ui()        

    def init_ui(self):
        '''
            Initialize the UI. Set the window size and call all initializing helper functions
        '''
        # Set the title and size of the application
        self.setWindowTitle('Integrating Process Lambda Tuner')
        self.setGeometry(100, 100, 700, 850)

        # Set the central widget and main vertical layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create all children widgets in the application
        self.create_menubar()
        self.create_plots()
        self.create_output_labels()
        self.show_startup_message()

    def create_menubar(self):
        '''
        Creates the menubar object with Load, Add Cursors, and Clear functions
        '''
        # Create a menu bar with a data field

        menubar = self.menuBar()
        steps = menubar.addMenu('Steps')

        # Create Load data action to trigger csv loading
        self.load_action = QAction('1. Load..', self)
        self.load_action.triggered.connect(self.load_data) # Replace with new callback
        steps.addAction(self.load_action) 

        # Create add cursors action to unlock user interaction with thecreate_plots plots
        self.add_cursors_action = QAction('2. Add Cursors..', self)
        self.add_cursors_action.triggered.connect(self.unlock_plots)
        self.add_cursors_action.setEnabled(False)
        steps.addAction(self.add_cursors_action) 

        # Calculate the system parameters
        self.calc_params_action = QAction('3. Calculate System Parameters..', self)
        self.calc_params_action.triggered.connect(self.calc_sys_params) 
        self.calc_params_action.setEnabled(False)
        steps.addAction(self.calc_params_action) 

        # Choose Lambda value
        self.choose_lambda_action = QAction('4. Choose Lambda Value..', self)
        self.choose_lambda_action.triggered.connect(self.show_lambda_input_popup) 
        self.choose_lambda_action.setEnabled(False)
        steps.addAction(self.choose_lambda_action) 

        # Calculate Gains
        self.calc_gains_action = QAction('5. Calculate Gains..', self)
        self.calc_gains_action.triggered.connect(self.calc_gains) 
        self.calc_gains_action.setEnabled(False)
        steps.addAction(self.calc_gains_action)

    def create_plots(self):
        '''
        Creates the duty cycle and process variable plots. Creates the navigation toolbar to control plot scaling
        '''
        # Create a Matplotlib Figure with 2 subplots (2 rows, 1 column)
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, sharex=True)

        # Create Matplotlib Canvas widget
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(700,600)
        self.layout.addWidget(self.canvas)

        # Set the titles and x labels of the plots
        self.ax1.set_title('CV')
        self.ax2.set_title('PV')
        self.ax2.set_xlabel('Time')

        # Adjust layout to prevent overlap of titles
        self.figure.tight_layout()

        # Connect the mouse press event to the function
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)

        # Add the toolbar to control the plots
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)

    def create_output_labels(self):
        '''
        Creates a dictionary of label objects for future manipulation. Applies alignment and adds widgets to the main app.
        '''
        self.hOutputLabels = QHBoxLayout()

        # Create separator vertical lines
        vline_frames = []
        for i in range(0,3):
            vline_frame = QFrame(self)
            vline_frame.setFrameShape(QFrame.VLine)
            vline_frame.setFrameShadow(QFrame.Sunken)
            vline_frames.append(vline_frame)

        # Initialize the horizontal layout output labels
        self.labels['delOutput'] = QLabel('∆Output: 0', self)
        self.labels['slope1'] = QLabel('Slope 1: 0', self)
        self.labels['slope2'] = QLabel('Slope 2: 0', self)
        self.labels['td'] = QLabel('Td: 0', self)
 
        # Apply alignment and add widgets to the horizontal layout
        i = 0
        for label in self.labels.values():
            label.setAlignment(Qt.AlignCenter)
            self.hOutputLabels.addWidget(label)
            if i < 3:
                self.hOutputLabels.addWidget(vline_frames[i])
                i+=1

        # Add the horizontal layout to the main widget
        self.layout.addLayout(self.hOutputLabels)

        # Initialize the vertical layout output labels
        self.labels['L'] = QLabel('Lambda, λ: 0', self)
        self.labels['Kp'] = QLabel('Process Gain, Kp: 0', self)
        self.labels['P'] = QLabel('Proportional Gain, P: 0', self)
        self.labels['It'] = QLabel('Integral Time, It: 0', self)

        # Create the horizontal divider line separating the horizontal layout
        line_frame = QFrame(self)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)

        # Set alignment on the labels and add widgets to the main layout
        self.labels['L'].setAlignment(Qt.AlignCenter)
        self.labels['Kp'].setAlignment(Qt.AlignCenter)
        self.labels['P'].setAlignment(Qt.AlignCenter)
        self.labels['It'].setAlignment(Qt.AlignCenter)
        self.layout.addWidget(line_frame)
        self.layout.addWidget(self.labels['L'])
        self.layout.addWidget(self.labels['Kp'])
        self.layout.addWidget(self.labels['P'])
        self.layout.addWidget(self.labels['It'])

    def show_startup_message(self):
        """
            Shows the startup message
        """
        message_box = QMessageBox()
        message_box.setWindowTitle('Integrating Process Lambda Tuner')
        message_box.setText('Select the Steps menu in the top left corner to work through the tuning')
        message_box.setIcon(QMessageBox.Information)
        message_box.exec_()

    def update_plots(self):
        """
        Update the plot with the new data from the csv
        """

        self.ax1.clear()
        self.ax1.plot(self.cv_x_data, self.cv_y_data, marker='o', linestyle='-', color='b', markersize=1, linewidth=0.8)
        self.ax1.set_title('CV')

        self.ax2.clear()
        self.ax2.plot(self.pv_x_data, self.pv_y_data, marker='o', linestyle='-', color='b', markersize=1, linewidth=0.8)
        self.ax2.set_title('PV')

        self.canvas.draw()

    def unlock_plots(self):
        '''
            Unlock the plot for user interaction
        '''
        # Allow user interaction with the plot 
        self.locked = False

    def clear_cursors(self):
        '''
            Clear all of the cursors on the plot
        '''

        # Iterate through the list of saved cursors and remove from the ax
        for line in self.lines:
            line.remove()

        # Clear all data members
        self.lines = []
        
        self.canvas.draw()

    def reset(self):
        '''
            Clear all contents on the plot
        '''
        self.clear_cursors()

        self.pv_x_data = []
        self.pv_y_data = []
        self.cv_x_data = []
        self.cv_y_data = []

        self.slope1 = 0
        self.slope2 = 0
        self.td = 0
        self.delOutput = 0
        self.pvTransPt = 0
        self.cvTransPt = 0
        self.locked = True
        self.dataLoaded = False
        
        self.ax1.clear()
        self.ax2.clear()

        # Set the titles and x labels of the plots
        self.ax1.set_title('CV')
        self.ax2.set_title('PV')
        self.ax2.set_xlabel('Time')

        # Reset the labels 
        self.labels['delOutput'].setText('∆Output: 0')
        self.labels['slope1'].setText('Slope 1: 0')
        self.labels['slope2'].setText('Slope 2: 0')
        self.labels['td'].setText('Td: 0')

        self.canvas.draw()

    def on_canvas_click(self, event):
        """
            Adds a cursor to the plot if interaction is unlocked. If the maximum number of cursors
            has been drawn, lock user interaction with the plot.
        """
        if (event.inaxes == self.ax2 and not self.locked):
            cursorColor = 'red' if len(self.lines) < 2 else 'blue'
            line = self.ax2.axvline(x=event.xdata, color=cursorColor, linestyle='--', linewidth=0.8)
            self.lines.append(line)
            self.canvas.draw()

        if len(self.lines) == 4:
            self.locked = True
            self.add_cursors_action.setEnabled(False)
            self.calc_params_action.setEnabled(True)

    def load_data(self):
        """
            Load data from csv file into the plot. Populate the internal x_data and y_data fields
        """
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filePath, _ = QFileDialog.getOpenFileName(self, "Load CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)

        if filePath:
            try:
                data = np.genfromtxt(filePath, delimiter=',')
                self.pv_x_data = data[:, 0]
                self.cv_x_data = data[:, 0]
                self.pv_y_data = data[:, 1]
                self.cv_y_data = data[:, 2]
                self.update_plots()
                self.load_action.setEnabled(False)
                self.add_cursors_action.setEnabled(True)
            except Exception as e:
                print(f"Error loading data: {e}")

    def calc_sys_params(self):
        """
            Calculate the system parameters
        """
        self.find_slopes()
        self.find_del_output()
        self.find_td()
        self.calc_params_action.setEnabled(False)
        self.choose_lambda_action.setEnabled(True)

    def find_slopes(self):
        """
            Finds the two slopes defining the system and the process variable transistion time
        """
        # Define the start and end values of each slice
        sl1Start = self.lines[0].get_xdata()[0]
        sl1End = self.lines[1].get_xdata()[0]
        sl2Start = self.lines[2].get_xdata()[0]
        sl2End = self.lines[3].get_xdata()[0]

        # Return the slice data
        sl1x, sl1y = self.slice_data(sl1Start, sl1End)
        sl2x, sl2y = self.slice_data(sl2Start, sl2End)

        # Clear the cursors from the plot
        self.clear_cursors()

        # Get the coefficients
        sl1_coeffs = np.polyfit(sl1x.flatten(), sl1y.flatten(), 1)
        sl2_coeffs = np.polyfit(sl2x.flatten(), sl2y.flatten(), 1)

        # Set the internal storage variables
        self.slope1 = np.round(sl1_coeffs[0], decimals=3)
        self.slope2 = np.round(sl2_coeffs[0], decimals=3)

        # Set the labels on the GUI
        self.labels['slope1'].setText('Slope 1: {}'.format(self.slope1))
        self.labels['slope2'].setText('Slope 2: {}'.format(self.slope2))
 
        # Find the points of intersection
        self.pvTransPt, inter_y = self.find_intersection_point(sl1_coeffs, sl2_coeffs)

        # Plot the intersection point
        self.ax2.plot(self.pvTransPt, inter_y, marker='o', color='r')

        self.canvas.draw()

    def find_intersection_point(self, line1, line2):
        """
            Finds the intersection point between the two lines
        """
        # Extract coefficients (slope and y-intercept) for each line
        m1, b1 = line1
        m2, b2 = line2

        # Solve the system of linear equations to find the intersection point
        x_intersection = (b2 - b1) / (m1 - m2)
        y_intersection = m1 * x_intersection + b1

        return x_intersection, y_intersection

    def slice_data(self, start, end):
        """
            Slice the x and y data using the cursors start and end positions
        """
        slIndices = np.where(((self.pv_x_data) >= start) & (self.pv_x_data <= end))
        slx = self.pv_x_data[slIndices]     
        sly = self.pv_y_data[slIndices]
        return slx, sly

    def find_del_output(self):
        """
            Finds the command output transition point and control value transition time
        """
        prev_val = self.cv_y_data[0]
        for i, val in enumerate(self.cv_y_data):
            curr_val = val
            if curr_val != prev_val:
                cvTransPtIdx = i-1
                self.del_output = np.round(curr_val - prev_val, decimals=3)
            prev_val = curr_val

        # Set the cvTransPt value
        self.cvTransPt = self.cv_x_data[cvTransPtIdx]

        # Plot the command transition point
        self.ax1.plot(self.cv_x_data[cvTransPtIdx], self.cv_y_data[cvTransPtIdx], marker='o', color='r')
        self.canvas.draw()

        # Set the label on the GUI
        self.labels['delOutput'].setText('∆Output: {}'.format(self.del_output))

    def find_td(self):
        """
            Finds the dead time of the system
        """
        # Calculate the dead time
        self.td = np.round(self.pvTransPt - self.cvTransPt, decimals=3)

        # Set the label on the GUI
        self.labels['td'].setText('Td: {}'.format(self.td))

    def show_lambda_input_popup(self):
        """
            Show the lambda input popup
        """
        value, ok = QInputDialog.getText(self, 'Lambda Input', 'Enter the desired value:')

        if ok and value:
            self.lambdaVal = float(value)
            self.calc_gains_action.setEnabled(True)
            self.labels['L'].setText('Lambda, λ: {}'.format(self.lambdaVal))
        
    def calc_gains(self):
        """
            Calculate all of the lambda gains
        """
        self.processGain = np.round((self.slope2 - self.slope1)/self.del_output, decimals=4)
        pNumerator = 2*self.lambdaVal + self.td
        pDenomenator = self.processGain*((self.lambdaVal + self.td)**2)
        self.proportionalGain = np.round(pNumerator/pDenomenator, decimals=4)
        self.integralTime = np.round(pNumerator, decimals=4)

        self.labels['Kp'].setText('Process Gain, Kp: {}'.format(self.processGain))
        self.labels['P'].setText('Proportional Gain, P: {}'.format(self.proportionalGain))
        self.labels['It'].setText('Integral Time, It: {}'.format(self.integralTime))

def main():
    app = QApplication(sys.argv)
    lambdaTuner = LambdaTuner()
    lambdaTuner.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
