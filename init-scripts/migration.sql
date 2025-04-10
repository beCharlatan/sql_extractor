CREATE TABLE organizations (
    epk_id BIGINT PRIMARY KEY,
    inn VARCHAR(20) NOT NULL,
    org_name VARCHAR(4000),
    segment_id SMALLINT,
    holding_name VARCHAR(500),
    sector_name VARCHAR(250),
    industry_name VARCHAR(100),
    okwd VARCHAR(10),
    oktmo INTEGER,
    oksto INTEGER,
    district_name VARCHAR(250),
    region_name VARCHAR(250),
    town_name VARCHAR(250),
    is_military BOOLEAN,
    is_salary_agreement BOOLEAN,
    avg_fot_amt BIGINT,
    avg_fl_amt BIGINT,
    diff_fot_amt BIGINT,
    diff_fl_amt BIGINT,
    avg_salary_amt BIGINT,
    fl_amt_potential BIGINT,
    employee_count_amt BIGINT,
    role_14_saphr_id BIGINT,
    role_14_fio VARCHAR(150),
    role_14_tb_id SMALLINT,
    role_14_gosb_id INTEGER,
    role_14_boss_saphr_id BIGINT,
    role_14_is_absence BOOLEAN,
    role_14_vacation_start_dt DATE,
    role_14_vacation_end_dt DATE,
    role_73_saphr_id BIGINT,
    role_73_fio VARCHAR(150),
    role_73_tb_id SMALLINT,
    role_73_gosb_id INTEGER,
    role_73_boss_saphr_id BIGINT,
    role_73_is_absence BOOLEAN,
    role_73_vacation_start_dt DATE,
    role_73_vacation_end_dt DATE,
    role_6_saphr_id BIGINT,
    role_6_fio VARCHAR(150),
    role_6_tb_id SMALLINT,
    role_6_gosb_id INTEGER,
    last_activity_dt DATE,
    last_expansion_activity_dt DATE,
    last_salary_activity_dt DATE,
    last_outflow_activity_dt DATE,
    last_contact_activity_dt DATE
);


COMMENT ON COLUMN organizations.epk_id IS 'Идентификатор EПК';
COMMENT ON COLUMN organizations.inn IS 'ИНН';
COMMENT ON COLUMN organizations.org_name IS 'Наименование организации';
COMMENT ON COLUMN organizations.segment_id IS 'Идентификатор сегмента';
COMMENT ON COLUMN organizations.holding_name IS 'Наименование холдинга';
COMMENT ON COLUMN organizations.sector_name IS 'Наименование отрасли';
COMMENT ON COLUMN organizations.industry_name IS 'Наименование индустрии';
COMMENT ON COLUMN organizations.okwd IS 'OKS3A';
COMMENT ON COLUMN organizations.oktmo IS 'OKTMO';
COMMENT ON COLUMN organizations.oksto IS 'OKATO';
COMMENT ON COLUMN organizations.district_name IS 'Наименование района';
COMMENT ON COLUMN organizations.region_name IS 'Наименование региона';
COMMENT ON COLUMN organizations.town_name IS 'Наименование населенного пункта';
COMMENT ON COLUMN organizations.is_military IS 'Признак силовой организации';
COMMENT ON COLUMN organizations.is_salary_agreement IS 'Признак зарплатного соглашения';
COMMENT ON COLUMN organizations.avg_fot_amt IS 'Средний ФОТ за последние три месяца';
COMMENT ON COLUMN organizations.avg_fl_amt IS 'Средний портфель ФЛ за последние три месяца';
COMMENT ON COLUMN organizations.diff_fot_amt IS 'Разница ФОТ за последние шесть месяцев';
COMMENT ON COLUMN organizations.diff_fl_amt IS 'Разница портфеля ФЛ за последние шесть месяцев';
COMMENT ON COLUMN organizations.avg_salary_amt IS 'Средняя ЗП';
COMMENT ON COLUMN organizations.fl_amt_potential IS 'Потенциал';
COMMENT ON COLUMN organizations.employee_count_amt IS 'Численность сотрудников в организации';
COMMENT ON COLUMN organizations.role_14_saphr_id IS 'Табельный номер сотрудника с ролью 14';
COMMENT ON COLUMN organizations.role_14_fio IS 'ФИО сотрудника с ролью 14';
COMMENT ON COLUMN organizations.role_14_tb_id IS 'Идентификатор ТБ сотрудника';
COMMENT ON COLUMN organizations.role_14_gosb_id IS 'Идентификатор ГОСБ сотрудника с ролью 14';
COMMENT ON COLUMN organizations.role_73_saphr_id IS 'Табельный номер сотрудника с ролью 73';
COMMENT ON COLUMN organizations.role_73_fio IS 'ФИО сотрудника с ролью 73';
COMMENT ON COLUMN organizations.role_73_tb_id IS 'Идентификатор ТБ сотрудника с ролью 73';
COMMENT ON COLUMN organizations.role_73_gosb_id IS 'Идентификатор ГОСБ сотрудника с ролью 73';
COMMENT ON COLUMN organizations.role_6_saphr_id IS 'Табельный номер сотрудника с ролью 6';
COMMENT ON COLUMN organizations.role_6_fio IS 'ФИО сотрудника с ролью 6';
COMMENT ON COLUMN organizations.role_6_tb_id IS 'Идентификатор ТБ сотрудника с ролью 6';
COMMENT ON COLUMN organizations.role_6_gosb_id IS 'Идентификатор ГОСБ сотрудника с ролью 6';
COMMENT ON COLUMN organizations.role_14_boss_saphr_id IS 'Табельный номер связанного руководителя для сотрудника с ролью 14';
COMMENT ON COLUMN organizations.role_73_boss_saphr_id IS 'Табельный номер связанного руководителя для сотрудника с ролью 73';
COMMENT ON COLUMN organizations.role_14_is_absence IS 'Признак отсутствия для сотрудника с ролью 14';
COMMENT ON COLUMN organizations.role_73_is_absence IS 'Признак отсутствия для сотрудника с ролью 73';
COMMENT ON COLUMN organizations.role_14_vacation_start_dt IS 'Дата начала планового отпуска ближайшего для сотрудника с ролью 14';
COMMENT ON COLUMN organizations.role_14_vacation_end_dt IS 'Дата окончания планового отпуска ближайшего для сотрудника с ролью 14';
COMMENT ON COLUMN organizations.role_73_vacation_start_dt IS 'Дата начала планового отпуска ближайшего для сотрудника с ролью 73';
COMMENT ON COLUMN organizations.role_73_vacation_end_dt IS 'Дата окончания планового отпуска ближайшего для сотрудника с ролью 73';
COMMENT ON COLUMN organizations.last_activity_dt IS 'Дата последней активности по организации';
COMMENT ON COLUMN organizations.last_expansion_activity_dt IS 'Дата последней активности типа "Расширение зарплатного договора" по организации';
COMMENT ON COLUMN organizations.last_salary_activity_dt IS 'Дата последней активности типа "Зарплатный договор" по организации';
COMMENT ON COLUMN organizations.last_outflow_activity_dt IS 'Дата последней активности типа "Отток" по организации';
COMMENT ON COLUMN organizations.last_contact_activity_dt IS 'Дата последней активности типа "Контактная политика" по организации';