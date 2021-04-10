CREATE TABLE `daily_price_month` (
	`code` VARCHAR(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`code`, `date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;



----------------------------------------

CREATE TABLE `daily_price_week` (
	`code` VARCHAR(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`week` SMALLINT(6) NOT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`code`, `week`, `date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;


----------------------------------------

CREATE TABLE `daily_price_day` (
	`code` VARCHAR(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`week` SMALLINT(6) NULL DEFAULT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`code`, `date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;


----------------------------------------

CREATE TABLE `daily_price_min` (
	`code` VARCHAR(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`week` SMALLINT(6) NULL DEFAULT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`code`, `date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;


----------------------------------------

CREATE TABLE `daily_price_tick` (
	`code` VARCHAR(20) NOT NULL,
	`dailyCount` BIGINT(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`week` SMALLINT(6) NULL DEFAULT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`code`, `dailyCount`, `date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;

