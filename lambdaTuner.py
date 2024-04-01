import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QAction, QFileDialog, QInputDialog
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np
import csv

class LambdaTuner(QMainWindow):
    def __init__(self):
        super().__init__()

        # GUI data
        self.lines = []
        self.labels = {}
        self.locked = True

        # Intialize the PV and CV data arrays
        self.pv_x_data = []
        self.pv_y_data = []
        self.cv_x_data = []
        self.cv_y_data = []

        # Display units
        self.pvUnits = ''
        self.cvUnits = ''
        self.timeUnits = ''

        # Initializa the system parameters and gains
        self.slope1 = 0
        self.slope2 = 0
        self.td = 0
        self.delOutput = 0
        self.pvTransPt = 0
        self.cvTransPt = 0
        self.lambdaVal = 0
        self.processGain = 0
        self.proportionalGain = 0
        self.integralGain = 0
        self.integralTime = 0

        self.init_ui()        

    def init_ui(self):
        '''
            Initialize the UI. Set the window size and call all initializing helper functions
        '''
        # Set the title and size of the application
        self.setWindowTitle('Integrating Process Lambda Tuner')
        self.setFixedSize(900, 965)

        # Set the central widget and main vertical layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create all children widgets in the application
        self.create_menubar()
        self.create_plots()
        self.create_output_labels()

    def create_menubar(self):
        '''
        Creates the menubar object with Steps field to move through the application
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

        # Calculate the system parameters based on the cursor locations
        self.calc_params_action = QAction('3. Calculate System Parameters..', self)
        self.calc_params_action.triggered.connect(self.calc_sys_params) 
        self.calc_params_action.setEnabled(False)
        steps.addAction(self.calc_params_action) 

        # Choose Lambda value for the gain calculations
        self.choose_lambda_action = QAction('4. Choose Lambda Value and Calculate Gains..', self)
        self.choose_lambda_action.triggered.connect(self.show_lambda_input_popup) 
        self.choose_lambda_action.setEnabled(False)
        steps.addAction(self.choose_lambda_action)

    def create_plots(self):
        '''
        Creates the duty cycle and process variable plots. Creates the navigation toolbar to control plot scaling
        '''
        # Create a Matplotlib Figure with 2 subplots (2 rows, 1 column)
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, sharex=True)

        # Create Matplotlib Canvas widget
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(875,700)
        self.layout.addWidget(self.canvas)

        # Set the titles and x labels of the plots
        self.ax1.set_title('CV')
        self.ax1.set_xlabel('Time')
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
        for i in range(0,4):
            vline_frame = QFrame(self)
            vline_frame.setFrameShape(QFrame.VLine)
            vline_frame.setFrameShadow(QFrame.Sunken)
            vline_frames.append(vline_frame)

        # Initialize the horizontal layout output labels
        self.labels['delOutput'] = QLabel('∆Output: 0', self)
        self.labels['slope1'] = QLabel('Slope 1: 0', self)
        self.labels['slope2'] = QLabel('Slope 2: 0', self)
        self.labels['td'] = QLabel('Td: 0', self)
        self.labels['Kp'] = QLabel('Kp: 0', self)
 
        # Apply alignment and add widgets to the horizontal layout
        i = 0
        for label in self.labels.values():
            label.setAlignment(Qt.AlignCenter)
            self.hOutputLabels.addWidget(label)
            if i < 4:
                self.hOutputLabels.addWidget(vline_frames[i])
                i+=1

        # Add the horizontal layout to the main widget
        self.layout.addLayout(self.hOutputLabels)

        # Initialize the vertical layout output labels
        self.labels['L'] = QLabel('Lambda, λ: 0', self)
        self.labels['P'] = QLabel('Proportional Gain, P: 0', self)
        self.labels['It'] = QLabel('Integral Time, It: 0', self)
        self.labels['I'] = QLabel('Integral Gain, I: 0', self)

        # Create the horizontal divider line separating the horizontal layout
        line_frame = QFrame(self)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)

        # Set alignment on the labels and add widgets to the main layout
        self.labels['L'].setAlignment(Qt.AlignCenter)
        self.labels['P'].setAlignment(Qt.AlignCenter)
        self.labels['It'].setAlignment(Qt.AlignCenter)
        self.labels['I'].setAlignment(Qt.AlignCenter)
        self.layout.addWidget(line_frame)
        self.layout.addWidget(self.labels['L'])
        self.layout.addWidget(self.labels['P'])
        self.layout.addWidget(self.labels['It'])
        self.layout.addWidget(self.labels['I'])

    def update_plots(self):
        """
        Update the plot with the new data from the csv
        """
        self.ax1.clear()
        self.ax1.plot(self.cv_x_data, self.cv_y_data, marker='o', linestyle='-', color='b', markersize=1, linewidth=0.8)
        self.ax1.set_title('CV')
        self.ax1.set_xlabel('Time (' + self.timeUnits + ')')
        self.ax1.set_ylabel(self.cvUnits)

        self.ax2.clear()
        self.ax2.plot(self.pv_x_data, self.pv_y_data, marker='o', linestyle='-', color='b', markersize=1, linewidth=0.8)
        self.ax2.set_title('PV')
        self.ax2.set_xlabel('Time (' + self.timeUnits + ')')
        self.ax2.set_ylabel(self.pvUnits)

        self.canvas.draw()

    def unlock_plots(self):
        '''
            Unlock the plot for user interaction
        '''
        # Allow user interaction with the plot 
        self.locked = False

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
                # Import the data from the 
                data = np.genfromtxt(filePath, delimiter=',')
                self.pv_x_data = data[:, 0]
                self.cv_x_data = data[:, 0]
                self.pv_y_data = data[:, 1]
                self.cv_y_data = data[:, 2]

                # Get the headers from the csv
                with open(filePath, 'r') as file:
                    csv_reader = csv.reader(file)
                    headers = next(csv_reader)

                # Parse the headers
                units = []
                for i, header in enumerate(headers):
                    idx1 = header.index('(')
                    idx2 = header.index(')')
                    units.append(header[idx1+1:idx2])

                # Unpack found units into storage variables
                self.timeUnits, self.pvUnits, self.cvUnits= units

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
        self.find_process_gain()
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
        self.slope1 = sl1_coeffs[0]
        self.slope2 = sl2_coeffs[0]

        # Grab the limits on the current view
        ax2xLims = self.ax2.get_xlim()
        ax2yLims = self.ax2.get_ylim()

        # Create an array for new line
        # Generate x values within the xlim range
        sl1_x = np.linspace(ax2xLims[0], ax2xLims[1], 100)  
        sl2_x = np.linspace(ax2xLims[0], ax2xLims[1], 100)  

        # Calculate corresponding y values based on the equation
        sl1_y = sl1_coeffs[0] * sl1_x + sl1_coeffs[1]
        sl2_y = sl2_coeffs[0] * sl2_x + sl2_coeffs[1]

        # Find all indices that outside the viewport limits
        sl1_indices = np.where((sl1_y >= ax2yLims[0]) & (sl1_y <= ax2yLims[1]))
        sl2_indices = np.where((sl2_y >= ax2yLims[0]) & (sl2_y <= ax2yLims[1]))

        # Plot the lines of best fit
        self.ax2.plot(sl1_x[sl1_indices], sl1_y[sl1_indices], color='red', linestyle='--', linewidth='0.8')
        self.ax2.plot(sl2_x[sl2_indices], sl2_y[sl2_indices], color='red', linestyle='--', linewidth='0.8')

        # Set the labels on the GUI
        self.labels['slope1'].setText('Slope 1: {} '.format(np.round(self.slope1*1000, decimals=4)) + self.pvUnits + '/' + self.timeUnits)
        self.labels['slope2'].setText('Slope 2: {} '.format(np.round(self.slope2*1000, decimals=4)) + self.pvUnits + '/' + self.timeUnits)
 
        # Find the points of intersection
        self.pvTransPt, inter_y = self.find_intersection_point(sl1_coeffs, sl2_coeffs)

        self.ax2.axvline(x=self.pvTransPt, color='green', linestyle='--', linewidth='0.8')

        self.ax2.plot()

        # Plot the intersection point
        self.ax2.plot(self.pvTransPt, inter_y, marker='o', color='r')

        self.canvas.draw()

    def find_del_output(self):
        """
            Finds the command output transition point and control value transition time
        """
        prev_val = self.cv_y_data[0]
        for i, val in enumerate(self.cv_y_data):
            curr_val = val
            if curr_val != prev_val:
                cvTransPtIdx = i-1
                self.del_output = curr_val - prev_val
            prev_val = curr_val

        # Set the cvTransPt value
        self.cvTransPt = self.cv_x_data[cvTransPtIdx]

        # Plot the veritcal lines for the intersection with Td
        self.ax1.axvline(x=self.cvTransPt, color='green', linestyle='--', linewidth='0.8')
        self.ax2.axvline(x=self.cvTransPt, color='green', linestyle='--', linewidth='0.8')

        # Plot the command transition point
        self.ax1.plot(self.cv_x_data[cvTransPtIdx], self.cv_y_data[cvTransPtIdx], marker='o', color='r')
        self.canvas.draw()

        # Set the label on the GUI
        self.labels['delOutput'].setText('∆Output: {} '.format(np.round(self.del_output, decimals=8)) + self.cvUnits)

    def find_td(self):
        """
            Finds the dead time of the system
        """
        # Calculate the dead time
        self.td = self.pvTransPt - self.cvTransPt                            

        # Set the label on the GUI
        self.labels['td'].setText('Td: {} '.format(np.round(self.td, decimals=4)) + self.timeUnits)

    def find_process_gain(self):
        """
        Calculate the process gain based on the found system parameters
        """
        # Calculate the process gain
        self.processGain = (self.slope2 - self.slope1)/self.del_output
        self.labels['Kp'].setText('Kp: {}'.format(np.round(self.processGain, decimals=8)))

    def show_lambda_input_popup(self):
        """
            Show the lambda input popup, reset the label value, and call the gain calculation function
        """
        value, ok = QInputDialog.getText(self, '', 'Enter the Lambda (λ) value: (Units: {}) \n\n Minimum Value (3*Td): {}'.format(self.timeUnits, np.round(3*self.td, decimals=2)))
        if ok and value:
            value = value.replace(",","")                                    # Strip out commas from the lambda input if formatted incorrectly
            self.lambdaVal = float(value)                               # Convert the str s input to float ms
            self.labels['L'].setText('Lambda, λ: {}'.format(self.lambdaVal)) # Update the lambda label on the application
            self.calc_gains()                                                # Calculate the lambda tuning gains
        
    def calc_gains(self):
        """
            Calculate all of the lambda tuning gains
        """
        # Calculate the proportional gain
        pNumerator = 2*self.lambdaVal + self.td
        pDenomenator = self.processGain*((self.lambdaVal + self.td)**2)
        self.proportionalGain = pNumerator/pDenomenator

        # Calculate the integral time
        self.integralTime = pNumerator
        
        # Calculate the integral gain
        self.integralGain = self.proportionalGain/self.integralTime

        # Update the labels on the application
        self.labels['P'].setText('Proportional Gain, P: {}'.format(np.round(self.proportionalGain, decimals=6)))
        self.labels['It'].setText('Integral Time, It: {} '.format(np.round(self.integralTime, decimals=4)) + self.timeUnits)
        self.labels['I'].setText('Integral Gain, I: {}'.format(np.round(self.integralGain, decimals=6)))

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

def main():
    app = QApplication(sys.argv)
    lambdaTuner = LambdaTuner()
    lambdaTuner.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
