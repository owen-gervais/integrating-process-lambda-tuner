# Integrating Process Lambda Tuner

The Integrating Process Lambda Tuner is a simple commissioning tool designed to provide baseline PI gains for integrating process control loops.

## Overview

While commissioning an integrating process PI control loop, a common initial approach is to embark on a trial-and-error path, adjusting the proportional term (P) either up or down to achieve a response close to the desired one, and subsequently incorporating the integral term (I) to address steady-state error. Although this iterative process eventually yields a solution, it comes at the cost of significant time investment, as one must stumble through until arriving at the correct values for P and I.

Lambda tuning offers an alternative method by numerically computing baseline PI gains based on a user-defined arrest time (Lambda). However, to complete this process effectively, it's crucial to identify key system parameters.

The Integrating Process Lambda Tuner simplifies this process by providing an intuitive interface to analyze and optimize Lambda function configurations based on historical usage patterns and performance metrics.

## Features

- **Automatic System Parameter Identification**: Input a PV/CV dataset and the place cursors on the two slopes to quickly identify the system parameters.
- **PI Gain Calculation**: Input a desired Lambda value (arrest time) and the system will use the found parameters to calculate your gains.

## Getting Started

To get started with the Integrating Process Lambda Tuner, follow these steps:

1. **Clone the Repository**: Clone the Integrating Process Lambda Tuner repository to your local machine.

    ```
    git clone https://github.com/yourusername/integrating-process-lambda-tuner.git
    ```

2. **Install Dependencies**: Install the required dependencies using the below command

    ```
    pip install PyQt5
    pip install numpy
    pip install matplotlib
    ```

## License

The Lambda Tuner App is open-source software licensed under the [MIT License](LICENSE).
