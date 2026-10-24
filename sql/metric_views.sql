CREATE OR REPLACE VIEW "vw_m01_headcount" AS
SELECT month_start_date, department_id, headcount_end AS metric_value
FROM fact_headcount_monthly;

CREATE OR REPLACE VIEW "vw_m02_hires" AS
SELECT month_start_date, department_id, hires AS metric_value
FROM fact_headcount_monthly;

CREATE OR REPLACE VIEW "vw_m03_exits" AS
SELECT month_start_date, department_id, exits AS metric_value
FROM fact_headcount_monthly;

CREATE OR REPLACE VIEW "vw_m04_monthly_attrition_rate" AS
SELECT month_start_date, department_id,
       CASE WHEN headcount_start = 0 THEN NULL
            ELSE exits * 100.0 / headcount_start END AS metric_value
FROM fact_headcount_monthly;

CREATE OR REPLACE VIEW "vw_m05_rolling_12m_attrition" AS
SELECT month_start_date, department_id,
       CASE WHEN AVG(headcount_end) OVER (
                    PARTITION BY department_id ORDER BY month_start_date
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                ) = 0 THEN NULL
            ELSE SUM(exits) OVER (
                    PARTITION BY department_id ORDER BY month_start_date
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                 ) * 100.0 /
                 AVG(headcount_end) OVER (
                    PARTITION BY department_id ORDER BY month_start_date
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                 ) END AS metric_value
FROM fact_headcount_monthly;

CREATE OR REPLACE VIEW "vw_m06_voluntary_attrition_rate" AS
SELECT month_start_date, department_id,
       CASE WHEN AVG(headcount_end) OVER (
                    PARTITION BY department_id ORDER BY month_start_date
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                ) = 0 THEN NULL
            ELSE SUM(voluntary_exits) OVER (
                    PARTITION BY department_id ORDER BY month_start_date
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                 ) * 100.0 /
                 AVG(headcount_end) OVER (
                    PARTITION BY department_id ORDER BY month_start_date
                    ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                 ) END AS metric_value
FROM fact_headcount_monthly;

CREATE OR REPLACE VIEW "vw_m07_gross_pay" AS
SELECT period_end_date AS month_end, department_id,
       SUM(gross_pay) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_payroll GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m08_net_pay" AS
SELECT period_end_date AS month_end, department_id,
       SUM(net_pay) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_payroll GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m09_employer_payroll_cost" AS
SELECT period_end_date AS month_end, department_id,
       SUM(employer_cost) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_payroll GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m10_cost_per_head" AS
SELECT period_end_date AS month_end, department_id,
       SUM(employer_cost) / NULLIF(COUNT(DISTINCT employee_id), 0) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_payroll GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m11_overtime_share" AS
SELECT period_end_date AS month_end, department_id,
       SUM(overtime_pay) * 100.0 / NULLIF(SUM(employer_cost), 0) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_payroll GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m12_variable_pay_share" AS
SELECT period_end_date AS month_end, department_id,
       SUM(variable_pay) * 100.0 / NULLIF(SUM(gross_pay), 0) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_payroll GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m13_attendance_rate" AS
SELECT period_end_date AS month_end, department_id,
       (SUM(present_days) + 0.5 * SUM(half_days_unpaid)) /
       NULLIF(SUM(scheduled_days), 0) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_attendance_monthly GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m14_late_arrival_rate" AS
SELECT period_end_date AS month_end, department_id,
       SUM(late_arrivals) * 1.0 / NULLIF(SUM(present_days), 0) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_attendance_monthly GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m15_leave_without_pay_days" AS
SELECT period_end_date AS month_end, department_id,
       SUM(lop_days) AS metric_value,
       COUNT(DISTINCT employee_id) AS employee_count
FROM fact_payroll GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m22_task_completion_rate" AS
SELECT team_id, sprint_id,
       COUNT(*) FILTER (WHERE status = 'Done') * 1.0 /
       NULLIF(COUNT(*) FILTER (WHERE status <> 'Cancelled'), 0) AS metric_value,
       COUNT(*) FILTER (WHERE status <> 'Cancelled') AS task_count
FROM fact_task GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m23_on_time_delivery_rate" AS
SELECT team_id, sprint_id,
       COUNT(*) FILTER (WHERE completed_on_time = 'Y') * 1.0 /
       NULLIF(COUNT(*) FILTER (WHERE status = 'Done'), 0) AS metric_value,
       COUNT(*) FILTER (WHERE status = 'Done') AS task_count
FROM fact_task GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m24_velocity" AS
SELECT team_id, sprint_id,
       SUM(story_points) FILTER (WHERE status = 'Done') AS metric_value,
       COUNT(*) FILTER (WHERE status = 'Done') AS task_count
FROM fact_task GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m25_average_cycle_time" AS
SELECT team_id, sprint_id,
       AVG(cycle_time_days) FILTER (WHERE status = 'Done') AS metric_value,
       COUNT(*) FILTER (WHERE status = 'Done') AS task_count
FROM fact_task GROUP BY 1, 2;

CREATE OR REPLACE VIEW "vw_m27_high_risk_share" AS
SELECT department_id,
       COUNT(*) FILTER (WHERE risk_band = 'High') * 1.0 /
       NULLIF(COUNT(*), 0) AS metric_value,
       COUNT(*) AS employee_count
FROM fact_attrition_risk GROUP BY department_id;