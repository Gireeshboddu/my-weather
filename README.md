This project presents an automated weather data extraction, transformation, and forecasting pipeline using Apache Airflow, Weather API, and AWS S3. The system fetches historical weather data hourly, predicts future temperatures using machine learning (Random Forest Regression), stores the data in cloud storage, and generates comprehensive visualizations. By fully automating the ETL process, this system ensures scalable, reliable, and near real-time forecasting suitable for smart applications.
In addition to automation, the pipeline emphasizes modularity, making it adaptable for different locations and forecasting horizons. The integration with AWS S3 provides centralized, cloud-based access to data and visual outputs, enabling downstream use in dashboards or alerting systems. With a focus on maintainability and extensibility, the system is built using containerized services orchestrated through Docker, ensuring smooth deployment across different environments. Overall, this solution demonstrates a practical approach to time-series forecasting and real-time data engineering in a production-ready set-up.




Python
Python served as the backbone of this project, enabling rapid development, flexibility, and integration across components. Core libraries such as Pandas were used for data manipulation and cleaning, while Matplotlib was employed to generate high-quality visualizations of both actual and predicted weather values. For machine learning, Scikit-learn was utilized to train and evaluate a Random Forest Regression model that forecasts temperature based on time-series patterns. Additionally, Boto3, Amazon's SDK for Python, was used to interact with AWS S3 for uploading and downloading data files, ensuring seamless cloud storage integration.

Apache Airflow
Apache Airflow was the orchestration tool that transformed the project from a standalone script into a reliable, production-grade pipeline. It was used to define a DAG (Directed Acyclic Graph) that schedules and automates the ETL process. Running every hour, the DAG ensures consistent data extraction, transformation, prediction, visualization, and cloud upload without manual intervention. Airflow also provides a web interface for monitoring task statuses, managing retries, and viewing logs, which is essential for operational transparency and debugging.

Weather API
The Weather API acted as the primary data source for this project. Specifically, its historical endpoint was used to retrieve weather data—including hourly temperature and humidity—for the past 10 hours in Mount Pleasant. This API made it possible to simulate near-real-time forecasting by always working with the most recent data. The API’s JSON response was parsed and processed in the transformation stage before feeding into the regression model for prediction.
AWS S3
Amazon S3 was chosen as the cloud storage solution to persist both the raw and processed data. After each ETL run, the system uploads two CSV files—one containing the actual weather data and the other the predicted temperature—as well as the generated plot image. By storing these assets in S3, the data becomes accessible for downstream analysis, integration with dashboards, or long-term storage for auditing and research. Boto3 was used for all file transfer operations.

Docker Compose
To simplify deployment and ensure environment consistency across different systems, the project uses Docker Compose. It defines and manages the multi-container setup, including the Airflow scheduler, web server, worker, and PostgreSQL database. This approach eliminates dependency issues and provides an easy-to-replicate infrastructure that can be run with a single command (docker compose up). It also facilitates local testing and development before cloud deployment.

PostgreSQL
As required by Apache Airflow, a PostgreSQL database was used as the Airflow metadata store. This database keeps track of all the core components of the Airflow system, such as DAG definitions, task instance states, run logs, scheduling history, and configuration parameters. Although we did not manually write or run raw SQL queries against PostgreSQL in this project, Airflow internally performs a wide variety of SQL operations to maintain state and scheduling consistency.

To set up and use PostgreSQL in our environment, we relied on Docker Compose, which automatically provisions the Postgres container along with the necessary environment variables (username, password, database name). Here’s a breakdown of the relevant commands and their role:
Commands/Configuration Used:
In docker-compose.yml, the following environment variables initialize the PostgreSQL instance:
POSTGRES_USER: airflow
POSTGRES_PASSWORD: airflow
POSTGRES_DB: airflow

During Airflow initialization, the following command is executed to set up the Airflow database schema:
bash
CopyEdit
airflow db init

This command connects to PostgreSQL and creates all the necessary tables and metadata records required by Airflow.
To create an Airflow admin user (stored in the PostgreSQL backend), this command is used:
airflow users create \
  --username airflow \
  --password airflow \
  --firstname Air \
  --lastname Flow \
  --role Admin \
  --email airflow@example.com

Behind the scenes, every Airflow DAG run and task execution triggers PostgreSQL inserts and updates. For example:
•	DAG definition → stored in dag table
•	Task instance → inserted/updated in task_instance table
•	Log references → tracked in log table
Although these SQL operations are abstracted by Airflow, they are essential for DAG scheduling, execution tracking, and web UI functionalities. Without PostgreSQL, the orchestration logic wouldn’t have persistence or state management.
4. Architecture Workflow & ETL Process
The architecture of this weather forecasting system is built for automation, scalability, and clarity, following the Extract-Transform-Load (ETL) design pattern. The architecture consists of interconnected modules that extract real-time weather data, transform and analyze it, and load the results to cloud storage for long-term access. The entire workflow is orchestrated using Apache Airflow and visualized in the diagram below
 ![image](https://github.com/user-attachments/assets/fa8f1fbd-1e6d-4367-9d9a-1299966050fb)

The ETL process begins with data extraction from the WeatherAPI.com, which provides up-to-date hourly temperature and humidity data in JSON format. The system specifically queries the last 10 hours of weather history for Mount Pleasant, Michigan, USA to create a time window suitable for short-term forecasting.
In the transform stage, Python scripts are used to clean and preprocess the data. This includes converting timestamp values into localized Eastern Time, restructuring data into tabular format using pandas, and transforming the timestamps into UNIX epoch values to serve as numeric features for the prediction model. This step also incorporates time-series analysis using a machine learning model.
A Random Forest Regressor from the scikit-learn library is used during the prediction phase to forecast the temperature for the next hour. The model is trained using the most recent 10 hours of data, capturing short-term temporal patterns. Alongside the predicted temperature, an R² score is calculated to evaluate the model’s performance, offering insight into the reliability of the forecast.
Once the data is processed and the prediction is made, the load phase begins. The actual weather data, prediction results, and a dual-axis visualization plot are all saved as CSV files and PNG images. These outputs are then uploaded to an Amazon S3 bucket, ensuring centralized cloud storage and easy access for future use, such as dashboards, alerts, or reporting.
The visualization step generates a clear and insightful plot using matplotlib. It overlays historical temperature and humidity trends alongside predicted temperatures, using color-coded markers (blue dots for actuals, orange squares for humidity, red crosses for forecasts). Each data point is labeled to enhance interpretability, making the output useful for both technical users and stakeholders.
All the above steps are automated and orchestrated by Apache Airflow, a powerful workflow management platform. Airflow uses a Python-based Directed Acyclic Graph (DAG) to schedule and run each task on an hourly basis. It ensures consistent operation, handles retries in case of failure and provides a web-based interface to monitor job execution and logs.
By using this modular architecture, the system remains robust, maintainable, and scalable. It not only delivers real-time weather insights but also provides a production-ready template that can be extended to support more locations, longer prediction windows, or additional meteorological parameters.

File Architecture Overview
Below is an overview of the core files and their roles in the project, along with their placement in the working directory structure:
•	etl_weather.py is the heart of the pipeline, responsible for executing all ETL operations, including API calls, data transformation, machine learning, visualization, and file uploads.
•	weather_dag.py resides in the dags/ folder and defines the scheduling logic via Apache Airflow. It triggers the ETL script as a PythonOperator every hour.
•	requirements.txt ensures all dependencies are available inside the Docker container, including libraries for data science and AWS integration.
•	docker-compose.yml manages the setup of all services required to run Airflow, including PostgreSQL for metadata storage and the Airflow webserver.
•	/tmp directory is used temporarily by the ETL script to store outputs before uploading them to AWS S3. This includes weather data CSVs, forecast files, and graph images.

![image](https://github.com/user-attachments/assets/86b1ebba-f2d3-4796-986d-aecbebec13ac)

 Results
The implemented ETL pipeline successfully automates the end-to-end process of extracting, transforming, predicting, storing, and visualizing weather data. The system produces accurate and timely temperature forecasts each hour and makes them accessible via AWS S3. Below is a summary of key outcomes and insights derived from the pipeline:
Hourly Weather Forecasting
The system uses a Random Forest Regression model to predict the next hour's temperature based on the past 10 hours of data. The model's accuracy is evaluated using the R² (coefficient of determination) score, which is prominently displayed on the graph. In this particular run, the model achieved an R² score of 0.977, indicating a very strong fit between the predicted values and the actual trend.
Data Storage
After each forecast cycle, both the actual weather data and prediction results are stored as CSV files and visualized as PNG graphs. These outputs are uploaded to Amazon S3, enabling centralized cloud storage for long-term accessibility and integration into other platforms (e.g., dashboards or alert systems).
Comprehensive Visualization
 ![image](https://github.com/user-attachments/assets/b93fe2cd-bec9-47d9-820b-b26e4550db98)

The above graph is automatically generated during each ETL run and provides a detailed view of the most recent weather trends and forecasts. It includes the following elements:
•	🔵 Blue Line with Dots – Represents the actual recorded temperature (°C) over time. Each data point is labeled with its corresponding value for easy reference.
•	🟧 Orange Squares – Represent humidity (%) over the same time interval, plotted on a secondary Y-axis on the right. This allows both variables to be compared in the same chart without overlapping.
•	❌ Red Crosses – Show the predicted temperatures for future hours, derived from the Random Forest model. These points are labeled with their forecasted values (e.g., 21.9°C, 22.0°C, etc.).
•	🧠 Model Performance Indicator – The R² score is included at the bottom-right of the chart to provide a quick metric of model accuracy for that forecast run.
This visualization not only highlights the pipeline's capability to track real-time weather metrics but also emphasizes its forecasting accuracy and reliability in a production setting.
Automation Achieved
All these results—data extraction, prediction, CSV generation, visualization, and S3 upload—are fully automated via Apache Airflow. The DAG is configured to run on an hourly schedule, ensuring that the pipeline functions without manual intervention. Logs and DAG status are accessible through the Airflow web interface, providing transparency and control over operations.
Use Cases
This weather forecasting ETL pipeline demonstrates real-world utility across multiple domains. Here are five key use cases:
1. Smart Agriculture
Farmers can use hourly temperature predictions to make timely decisions about irrigation, pesticide application, and crop protection. Accurate short-term forecasts reduce the risk of weather-induced crop damage.
2. Logistics and Delivery Optimization
Weather-sensitive logistics companies can utilize the forecast to reroute deliveries, adjust schedules, or apply safeguards to goods, particularly in sectors like pharmaceuticals or food supply chains.
3. Smart Home Automation
IoT-enabled homes can use forecasted temperatures to proactively adjust heating or cooling systems, blinds, or ventilation—improving energy efficiency and occupant comfort.
4. Public Sector Planning
Local governments can integrate these forecasts into energy load forecasting, road maintenance planning, or public event scheduling, especially during extreme weather conditions.
5. Weather Visualization Dashboards
The generated plots and predictions can be embedded in dashboards for public communication, school projects, or internal company monitoring tools, offering easy-to-understand visual insights.
