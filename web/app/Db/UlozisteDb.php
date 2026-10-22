<?php
/* Administrace v MariaDB. Stav (co člověk přepsal) je jeden dokument — tak ho
   drží i ukázka v prohlížeči, takže se obě verze chovají stejně. Uživatelé a
   poptávky mají vlastní tabulky. */

declare(strict_types=1);

namespace App\Db;

use App\Api\Uloziste;
use App\Obsah\Stav;

final class UlozisteDb implements Uloziste
{
    private const STAV_ID = 1;

    public function __construct(private readonly \PDO $pdo)
    {
    }

    public function stav(): array
    {
        $radek = $this->pdo
            ->query('SELECT dokument FROM stav WHERE id = ' . self::STAV_ID)
            ->fetch();
        // Vždycky plný tvar: z prázdného POLE by si administrace vzala
        // stav.texts === undefined a spadla by hned po instalaci.
        if ($radek === false) {
            return Stav::prazdny();
        }
        $data = json_decode((string) $radek['dokument'], true);

        return is_array($data) && $data !== [] ? $data : Stav::prazdny();
    }

    public function ulozStav(array $stav, string $kdo): void
    {
        $stav['updatedAt'] = gmdate('Y-m-d\TH:i:s.000\Z');
        $dokument = json_encode($stav, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
        $kdy = date('Y-m-d H:i:s');

        $this->pdo->beginTransaction();
        try {
            $this->pdo->prepare(
                'INSERT INTO stav (id, dokument, zmeneno, kdo) VALUES (?, ?, ?, ?)
                 ON DUPLICATE KEY UPDATE dokument = VALUES(dokument), zmeneno = VALUES(zmeneno), kdo = VALUES(kdo)'
            )->execute([self::STAV_ID, $dokument, $kdy, $kdo]);
            $this->pdo->prepare('INSERT INTO stav_historie (dokument, zmeneno, kdo) VALUES (?, ?, ?)')
                ->execute([$dokument, $kdy, $kdo]);
            $this->pdo->commit();
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }

    public function uzivatele(): array
    {
        return $this->pdo->query(
            'SELECT id, jmeno, email, role, aktivni, vytvoreno, posledni_prihlaseni,
                    pozvanka_token IS NOT NULL AND heslo_hash IS NULL AS ceka_na_pozvanku
             FROM uzivatele ORDER BY id'
        )->fetchAll();
    }

    public function ulozUzivatele(array $u): array
    {
        $id = isset($u['id']) ? (int) $u['id'] : 0;
        $sloupce = ['jmeno', 'email', 'role', 'aktivni', 'heslo_hash', 'pozvanka_token', 'pozvanka_do'];

        if ($id > 0) {
            $nastav = [];
            $hodnoty = [];
            foreach ($sloupce as $s) {
                if (array_key_exists($s, $u)) {
                    $nastav[] = "{$s} = ?";
                    $hodnoty[] = $u[$s];
                }
            }
            if ($nastav !== []) {
                $hodnoty[] = $id;
                $this->pdo->prepare('UPDATE uzivatele SET ' . implode(', ', $nastav) . ' WHERE id = ?')
                    ->execute($hodnoty);
            }
        } else {
            $this->pdo->prepare(
                'INSERT INTO uzivatele (jmeno, email, role, aktivni, heslo_hash, pozvanka_token, pozvanka_do, vytvoreno)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
            )->execute([
                (string) ($u['jmeno'] ?? ''),
                (string) ($u['email'] ?? ''),
                (string) ($u['role'] ?? 'autor'),
                (int) ($u['aktivni'] ?? 1),
                $u['heslo_hash'] ?? null,
                $u['pozvanka_token'] ?? null,
                $u['pozvanka_do'] ?? null,
                date('Y-m-d H:i:s'),
            ]);
            $id = (int) $this->pdo->lastInsertId();
        }

        $radek = $this->podleId($id);
        return $radek ?? ($u + ['id' => $id]);
    }

    public function smazUzivatele(int $id): void
    {
        $this->pdo->prepare('DELETE FROM uzivatele WHERE id = ?')->execute([$id]);
    }

    public function uzivatelPodleJmena(string $jmeno): ?array
    {
        $dotaz = $this->pdo->prepare(
            'SELECT * FROM uzivatele WHERE email = ? OR jmeno = ? ORDER BY id LIMIT 1'
        );
        $dotaz->execute([$jmeno, $jmeno]);
        $radek = $dotaz->fetch();
        return $radek === false ? null : $radek;
    }

    /** Uživatel bez hashe hesla — to, co se smí poslat do prohlížeče. */
    public function podleId(int $id): ?array
    {
        $dotaz = $this->pdo->prepare(
            'SELECT id, jmeno, email, role, aktivni, vytvoreno, posledni_prihlaseni FROM uzivatele WHERE id = ?'
        );
        $dotaz->execute([$id]);
        $radek = $dotaz->fetch();
        return $radek === false ? null : $radek;
    }

    public function podleTokenu(string $token): ?array
    {
        $dotaz = $this->pdo->prepare('SELECT * FROM uzivatele WHERE pozvanka_token = ? LIMIT 1');
        $dotaz->execute([$token]);
        $radek = $dotaz->fetch();
        return $radek === false ? null : $radek;
    }

    public function zapisPrihlaseni(int $id): void
    {
        $this->pdo->prepare('UPDATE uzivatele SET posledni_prihlaseni = ? WHERE id = ?')
            ->execute([date('Y-m-d H:i:s'), $id]);
    }

    /** Poptávka z formuláře. Zůstává v databázi i když pošta nefunguje. */
    public function ulozPoptavku(array $p, bool $odeslano): int
    {
        $this->pdo->prepare(
            'INSERT INTO poptavky (prijato, typ, jmeno, email, telefon, zprava, vetev, jazyk, odeslano)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        )->execute([
            date('Y-m-d H:i:s'),
            (string) ($p['typ'] ?? ''),
            (string) ($p['jmeno'] ?? ''),
            (string) ($p['email'] ?? ''),
            (string) ($p['telefon'] ?? ''),
            (string) ($p['zprava'] ?? ''),
            (string) ($p['vetev'] ?? ''),
            (string) ($p['jazyk'] ?? 'cs'),
            $odeslano ? 1 : 0,
        ]);
        return (int) $this->pdo->lastInsertId();
    }

    /** Kolik poptávek přišlo za posledních $sekund sekund. */
    public function pocetPoptavekZa(int $sekund): int
    {
        $dotaz = $this->pdo->prepare(
            'SELECT COUNT(*) FROM poptavky WHERE prijato >= DATE_SUB(NOW(), INTERVAL ? SECOND)'
        );
        $dotaz->execute([max(1, $sekund)]);
        return (int) $dotaz->fetchColumn();
    }

    public function zapisUdalost(string $kdo, string $akce, string $detail = ''): void
    {
        $this->pdo->prepare('INSERT INTO udalosti (kdy, kdo, akce, detail) VALUES (?, ?, ?, ?)')
            ->execute([date('Y-m-d H:i:s'), $kdo, $akce, mb_substr($detail, 0, 255)]);
    }
}
