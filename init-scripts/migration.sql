CREATE TABLE products (
    epk_id INT8 PRIMARY KEY,
    inn VARCHAR(20) NOT NULL,
    org_name VARCHAR(4000),
    segment_id INT2,
    holding_name VARCHAR(500),
    sector_name VARCHAR(250),
    industry_name VARCHAR(500),
    okved VARCHAR(10),
    oktmo INT4,
    okato INT4,
    district_name VARCHAR(250),
    region_name VARCHAR(250),
    settlement_name VARCHAR(250),
    is_military BOOLEAN NOT NULL,
    is_salary_agreement BOOLEAN NOT NULL,
    m_3_avg_fot_amt INT8,
    m_3_avg_fl_qty INT8,
    y_diff_fot_amt INT8,
    y_diff_fl_amt INT8,
    avg_salary_amt INT8,
    potential_fl_qty INT8,
    employee_count_amt INT8,
    role_14_saphr_id INT8,
    role_14_tb_id INT2,
    role_14_gosb_id INT4,
    role_73_saphr_id INT8,
    role_73_tb_id INT2,
    role_73_gosb_id INT4,
    role_6_saphr_id INT8,
    role_6_tb_id INT2,
    role_6_gosb_id INT4,
    role_14_manager_saphr_id INT8,
    role_73_manager_saphr_id INT8,
    is_absence_role_14 BOOLEAN,
    is_absence_role_73 BOOLEAN,
    role_14_vacation_start_dt DATE,
    role_14_vacation_end_dt DATE,
    role_73_vacation_start_dt DATE,
    role_73_vacation_end_dt DATE,
    last_activity_dt DATE,
    last_expansion_activity_dt DATE,
    last_salary_activity_dt DATE,
    last_outflow_activity_dt DATE,
    last_contact_activity_dt DATE,
    all_required_attr_flag INT2,
    modified_dttm TIMESTAMP NOT NULL,
    data_version INT
);

COMMENT ON COLUMN products.epk_id IS 'Идентификатор ЕПК';

COMMENT ON COLUMN products.inn IS 'ИНН';

COMMENT ON COLUMN products.org_name IS 'Наименование организации';

COMMENT ON COLUMN products.segment_id IS 'Идентификатор сегмента';

COMMENT ON COLUMN products.holding_name IS 'Наименование холдинга';

COMMENT ON COLUMN products.sector_name IS 'Наименование отрасли';

COMMENT ON COLUMN products.industry_name IS 'Наименование индустрии';

COMMENT ON COLUMN products.okved IS 'ОКВЭД';

COMMENT ON COLUMN products.oktmo IS 'ОКТМО';

COMMENT ON COLUMN products.okato IS 'ОКАТО';

COMMENT ON COLUMN products.district_name IS 'Наименование района';

COMMENT ON COLUMN products.region_name IS 'Наименование региона';

COMMENT ON COLUMN products.settlement_name IS 'Наименование населенного пункта';

COMMENT ON COLUMN products.is_military IS 'Признак силовой организации';

COMMENT ON COLUMN products.is_salary_agreement IS 'Признак зарплатного договора';

COMMENT ON COLUMN products.m_3_avg_fot_amt IS 'Средний ФОТ за последние три месяца';

COMMENT ON COLUMN products.m_3_avg_fl_qty IS 'Средний портфель ФЛ за последние три месяца';

COMMENT ON COLUMN products.y_diff_fot_amt IS 'Изменение ФОТ за год';

COMMENT ON COLUMN products.y_diff_fl_amt IS 'Изменение портфеля ФЛ за год';

COMMENT ON COLUMN products.avg_salary_amt IS 'Средняя ЗП';

COMMENT ON COLUMN products.potential_fl_qty IS 'Потенциал ФЛ для организации';

COMMENT ON COLUMN products.employee_count_amt IS 'Численность сотрудников в организации';

COMMENT ON COLUMN products.role_14_saphr_id IS 'Табельный номер сотрудника с ролью 14';

COMMENT ON COLUMN products.role_14_tb_id IS 'Идентификатор ТБ сотрудника с ролью 14';

COMMENT ON COLUMN products.role_14_gosb_id IS 'Идентификатор ГОСБ сотрудника с ролью 14';

COMMENT ON COLUMN products.role_73_saphr_id IS 'Табельный номер сотрудника с ролью 73';

COMMENT ON COLUMN products.role_73_tb_id IS 'Идентификатор ТБ сотрудника с ролью 73';

COMMENT ON COLUMN products.role_73_gosb_id IS 'Идентификатор ГОСБ сотрудника с ролью 73';

COMMENT ON COLUMN products.role_6_saphr_id IS 'Табельный номер сотрудника с ролью 6';

COMMENT ON COLUMN products.role_6_tb_id IS 'Идентификатор ТБ сотрудника с ролью 6';

COMMENT ON COLUMN products.role_6_gosb_id IS 'Идентификатор ГОСБ сотрудника с ролью 6';

COMMENT ON COLUMN products.role_14_manager_saphr_id IS 'Табельный номер связанного руководителя для сотрудника с ролью 14';

COMMENT ON COLUMN products.role_73_manager_saphr_id IS 'Табельный номер связанного руководителя для сотрудника с ролью 73';

COMMENT ON COLUMN products.is_absence_role_14 IS 'Признак отсутствия для сотрудника с ролью 14';

COMMENT ON COLUMN products.is_absence_role_73 IS 'Признак отсутствия для сотрудника с ролью 73';

COMMENT ON COLUMN products.role_14_vacation_start_dt IS 'Дата начала планового отпуска ближайшего для сотрудника с ролью 14';

COMMENT ON COLUMN products.role_14_vacation_end_dt IS 'Дата окончания планового отпуска ближайшего для сотрудника с ролью 14';

COMMENT ON COLUMN products.role_73_vacation_start_dt IS 'Дата начала планового отпуска ближайшего для сотрудника с ролью 73';

COMMENT ON COLUMN products.role_73_vacation_end_dt IS 'Дата окончания планового отпуска ближайшего для сотрудника с ролью 73';

COMMENT ON COLUMN products.last_activity_dt IS 'Дата последней активности по организации';

COMMENT ON COLUMN products.last_expansion_activity_dt IS 'Дата последней активности типа "Расширение зарплатного договора" по организации';

COMMENT ON COLUMN products.last_salary_activity_dt IS 'Дата последней активности типа "Зарплатный договор" по организации';

COMMENT ON COLUMN products.last_outflow_activity_dt IS 'Дата последней активности типа "Отток" по организации';

COMMENT ON COLUMN products.last_contact_activity_dt IS 'Дата последней активности типа "Контактная политика" по организации';

COMMENT ON COLUMN products.modified_dttm IS 'Дата изменения';

COMMENT ON COLUMN products.data_version IS 'Версия загрузки файла';

CREATE TABLE ai_hub.mass_task_creation_le_data_desc (
    mass_task_creation_le_data_desc_pk SERIAL PRIMARY KEY,
    attr_name VARCHAR(200),
    description VARCHAR(500),
    weight FLOAT
);

INSERT INTO
    ai_hub.mass_task_creation_le_data_desc (
        attr_name,
        description,
        weight
    )
VALUES (
        'epk_id',
        'Идентификатор ЕПК (Единый профиль клиента) организации',
        NULL
    ),
    (
        'inn',
        'ИНН (Идентификационный номер налогоплательщика) организации',
        NULL
    ),
    (
        'org_name',
        'Наименование организации',
        NULL
    ),
    (
        'segment_id',
        'Идентификатор сегмента',
        NULL
    ),
    (
        'holding_name',
        'Наименование холдинга',
        NULL
    ),
    (
        'sector_name',
        'Наименование отрасли',
        NULL
    ),
    (
        'industry_name',
        'Наименование индустрии',
        NULL
    ),
    (
        'okved',
        'ОКВЭД (Общероссийский классификатор видов экономической деятельности) организации',
        NULL
    ),
    (
        'oktmo',
        'ОКТМО (Общероссийский классификатор территорий муниципальных образований) организации',
        NULL
    ),
    (
        'okato',
        'ОКАТО (Общероссийский классификатор объектов административно-территориального деления) организации',
        NULL
    ),
    (
        'district_name',
        'Наименование района',
        NULL
    ),
    (
        'region_name',
        'Наименование региона',
        NULL
    ),
    (
        'settlement_name',
        'Наименование населенного пункта',
        NULL
    ),
    (
        'is_military',
        'Признак силовой организации',
        NULL
    ),
    (
        'is_salary_agreement',
        'Признак зарплатного договора',
        NULL
    ),
    (
        'm_3_avg_fot_amt',
        'Средний ФОТ (Фонд оплаты труда) за последние три месяца',
        NULL
    ),
    (
        'm_3_avg_fl_qty',
        'Средний портфель ФЛ (Физических лиц) за последние три месяца',
        NULL
    ),
    (
        'y_diff_fot_amt',
        'Изменение ФОТ за год',
        NULL
    ),
    (
        'y_diff_fl_amt',
        'Изменение портфеля ФЛ за год',
        NULL
    ),
    (
        'avg_salary_amt',
        'Средняя ЗП (Заработная плата) организации',
        NULL
    ),
    (
        'potential_fl_qty',
        'Потенциал ФЛ для организации',
        NULL
    ),
    (
        'employee_count_amt',
        'Численность сотрудников в организации',
        NULL
    ),
    (
        'role_14_saphr_id',
        'Табельный номер сотрудника с ролью 14',
        NULL
    ),
    (
        'role_14_tb_id',
        'Идентификатор ТБ (Территориальный блок) сотрудника с ролью 14',
        NULL
    ),
    (
        'role_14_gosb_id',
        'Идентификатор ГОСБ (Государственный бюджет) сотрудника с ролью 14',
        NULL
    ),
    (
        'role_73_saphr_id',
        'Табельный номер сотрудника с ролью 73',
        NULL
    ),
    (
        'role_73_tb_id',
        'Идентификатор ТБ сотрудника с ролью 73',
        NULL
    ),
    (
        'role_73_gosb_id',
        'Идентификатор ГОСБ сотрудника с ролью 73',
        NULL
    ),
    (
        'role_6_saphr_id',
        'Табельный номер сотрудника с ролью 6',
        NULL
    ),
    (
        'role_6_tb_id',
        'Идентификатор ТБ сотрудника с ролью 6',
        NULL
    ),
    (
        'role_6_gosb_id',
        'Идентификатор ГОСБ сотрудника с ролью 6',
        NULL
    ),
    (
        'role_14_manager_saphr_id',
        'Табельный номер связанного руководителя для сотрудника с ролью 14',
        NULL
    ),
    (
        'role_73_manager_saphr_id',
        'Табельный номер связанного руководителя для сотрудника с ролью 73',
        NULL
    ),
    (
        'is_absence_role_14',
        'Признак отсутствия для сотрудника с ролью 14',
        NULL
    ),
    (
        'is_absence_role_73',
        'Признак отсутствия для сотрудника с ролью 73',
        NULL
    ),
    (
        'role_14_vacation_start_dt',
        'Дата начала планового отпуска ближайшего для сотрудника с ролью 14',
        NULL
    ),
    (
        'role_14_vacation_end_dt',
        'Дата окончания планового отпуска ближайшего для сотрудника с ролью 14',
        NULL
    ),
    (
        'role_73_vacation_start_dt',
        'Дата начала планового отпуска ближайшего для сотрудника с ролью 73',
        NULL
    ),
    (
        'role_73_vacation_end_dt',
        'Дата окончания планового отпуска ближайшего для сотрудника с ролью 73',
        NULL
    ),
    (
        'last_activity_dt',
        'Дата последней активности по организации',
        NULL
    ),
    (
        'last_expansion_activity_dt',
        'Дата последней активности типа "Расширение зарплатного договора" по организации',
        NULL
    ),
    (
        'last_salary_activity_dt',
        'Дата последней активности типа "Зарплатный договор" по организации',
        NULL
    ),
    (
        'last_outflow_activity_dt',
        'Дата последней активности типа "Отток" по организации',
        NULL
    ),
    (
        'last_contact_activity_dt',
        'Дата последней активности типа "Контактная политика" по организации',
        NULL
    );