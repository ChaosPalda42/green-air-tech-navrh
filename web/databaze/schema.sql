-- Green Air Tech — tabulky administrace (MariaDB 10.6+ / 11.x, utf8mb4).
-- Instalátor tento soubor přehraje; `Migrace` ho umí přehrát znovu, aniž by
-- něco přepsal (všechno je IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS stav (
  id            TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  dokument      LONGTEXT NOT NULL,
  zmeneno       DATETIME NOT NULL,
  kdo           VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

-- Historie: každé uložení se připíše, nic se nemaže. Kdyby někdo smazal text,
-- dá se vrátit.
CREATE TABLE IF NOT EXISTS stav_historie (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  dokument      LONGTEXT NOT NULL,
  zmeneno       DATETIME NOT NULL,
  kdo           VARCHAR(100) NOT NULL,
  KEY zmeneno (zmeneno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

CREATE TABLE IF NOT EXISTS uzivatele (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  jmeno               VARCHAR(100) NOT NULL,
  email               VARCHAR(190) NOT NULL,
  role                VARCHAR(20) NOT NULL,
  heslo_hash          VARCHAR(255) DEFAULT NULL,
  aktivni             TINYINT(1) NOT NULL DEFAULT 1,
  pozvanka_token      CHAR(64) DEFAULT NULL,
  pozvanka_do         DATETIME DEFAULT NULL,
  vytvoreno           DATETIME NOT NULL,
  posledni_prihlaseni DATETIME DEFAULT NULL,
  UNIQUE KEY email (email),
  KEY pozvanka_token (pozvanka_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

-- Poptávky z formuláře. Odesílají se e-mailem; tady zůstává záloha, aby se
-- zakázka neztratila, když pošta na serveru zlobí.
CREATE TABLE IF NOT EXISTS poptavky (
  id        INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  prijato   DATETIME NOT NULL,
  typ       VARCHAR(40) NOT NULL DEFAULT '',
  jmeno     VARCHAR(190) NOT NULL DEFAULT '',
  email     VARCHAR(190) NOT NULL DEFAULT '',
  telefon   VARCHAR(60) NOT NULL DEFAULT '',
  zprava    TEXT,
  vetev     VARCHAR(40) NOT NULL DEFAULT '',
  jazyk     CHAR(2) NOT NULL DEFAULT 'cs',
  odeslano  TINYINT(1) NOT NULL DEFAULT 0,
  KEY prijato (prijato)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;

-- Kdo se kdy přihlásil a co udělal. Krátká paměť pro případ sporu.
CREATE TABLE IF NOT EXISTS udalosti (
  id       INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  kdy      DATETIME NOT NULL,
  kdo      VARCHAR(100) NOT NULL DEFAULT '',
  akce     VARCHAR(40) NOT NULL,
  detail   VARCHAR(255) NOT NULL DEFAULT '',
  KEY kdy (kdy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_czech_ci;
