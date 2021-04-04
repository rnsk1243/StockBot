CREATE TABLE `daily_price_month` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`code` VARCHAR(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`id`, `code`),
	UNIQUE INDEX `date` (`date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;


----------------------------------------

CREATE TABLE `daily_price_week` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`code` VARCHAR(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`week` SMALLINT(6) NOT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`id`, `code`),
	UNIQUE INDEX `DATE` (`date`, `week`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;

----------------------------------------

CREATE TABLE `daily_price_day` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`code` VARCHAR(20) NOT NULL,
	`date` DATETIME NOT NULL,
	`week` SMALLINT(6) NULL DEFAULT NULL,
	`open` BIGINT(20) NULL DEFAULT NULL,
	`high` BIGINT(20) NULL DEFAULT NULL,
	`low` BIGINT(20) NULL DEFAULT NULL,
	`close` BIGINT(20) NULL DEFAULT NULL,
	`diff` BIGINT(20) NULL DEFAULT NULL,
	`volume` BIGINT(20) NULL DEFAULT NULL,
	PRIMARY KEY (`id`, `code`),
	UNIQUE INDEX `date` (`date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;

----------------------------------------

CREATE TABLE `daily_price_min` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
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
	PRIMARY KEY (`id`, `code`),
	UNIQUE INDEX `dailyCount` (`dailyCount`, `date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;

----------------------------------------

CREATE TABLE `daily_price_tick` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
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
	PRIMARY KEY (`id`, `code`),
	UNIQUE INDEX `dailyCount` (`dailyCount`, `date`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;