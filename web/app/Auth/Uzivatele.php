<?php
/* C-018 — uživatelé administrace: role, oprávnění, hesla a pozvánky.
   Matice práv odpovídá ukázce (data/content/cs.json → admin.uzivatele):
   správce vše, editor texty/realizace/novinky, autor jen novinky. */

declare(strict_types=1);

namespace App\Auth;

use App\Formular\Validace;

final class Uzivatele
{
    public const OBLASTI = ['texty', 'realizace', 'novinky', 'uzivatele', 'statistiky'];

    public const ROLE = [
        'spravce' => ['texty', 'realizace', 'novinky', 'uzivatele', 'statistiky'],
        'editor' => ['texty', 'realizace', 'novinky'],
        'autor' => ['novinky'],
    ];

    private const MIN_DELKA_HESLA = 12;

    /* Falešný hash pro ověření, když účet (nebo hash) v databázi není.
       Je to SKUTEČNÝ bcrypt (cost 12) k heslu, které nikdo nezná — ne
       vymyšlený řetězec: ten by mohl příští verze PHP odmítnout dřív, než
       začne počítat, a časový rozdíl mezi známým a neznámým jménem by se
       tiše vrátil. Konstanta je v JEDNODUCHÝCH uvozovkách ($2y by se v
       dvojitých bral jako proměnná) a nikdy se nepočítá za běhu. */
    private const FALESNY_HASH = '$2y$12$iUDAfChDSBNMmZf4pEaHeec/jmwAtEkhxCZVfSCelxUv7hFd2A3VS';

    /** Smí uživatel s danou rolí do dané oblasti? Neznámá role i oblast = ne. */
    public static function smi(string $role, string $oblast): bool
    {
        $role = self::ROLE[$role] ?? null;
        if ($role === null) {
            return false;
        }
        return in_array($oblast, $role, true);
    }

    /** Heslo se nikdy neukládá v čitelné podobě — jen hash se solí. */
    public static function hash(string $heslo): string
    {
        return password_hash($heslo, PASSWORD_DEFAULT);
    }

    /**
     * Ověří heslo proti uloženému hashu; neaktivní uživatel se nepřihlásí.
     * Účet může být i null (jméno v databázi není) — v takovém případě se
     * heslo stejně ověří proti falešnému hashi, aby trvání odpovědi prozrazovalo
     * jen heslo, ne existenci účtu.
     */
    public static function overHeslo(?array $uzivatel, string $heslo): bool
    {
        $hash = $uzivatel['heslo_hash'] ?? null;
        if (!is_string($hash) || $hash === '') {
            $hash = self::FALESNY_HASH;
        }
        $spravne = password_verify($heslo, $hash);
        if (!$spravne) {
            return false;
        }
        return ($uzivatel['aktivni'] ?? 0) == 1;
    }

    /** Kontrola síly hesla: null = v pořádku, jinak krátký důvod. */
    public static function zkontrolujHeslo(string $heslo): ?string
    {
        if (trim($heslo) === '') {
            return 'prazdne';
        }
        if (mb_strlen($heslo) < self::MIN_DELKA_HESLA) {
            return 'kratke';
        }
        return null;
    }

    /** Seznam jmen vadných polí ('jmeno', 'email', 'role'); prázdné = v pořádku. */
    public static function zkontroluj(array $uzivatel): array
    {
        $vady = [];

        $jmeno = $uzivatel['jmeno'] ?? null;
        if (!is_string($jmeno) || trim($jmeno) === '') {
            $vady[] = 'jmeno';
        }

        $email = $uzivatel['email'] ?? null;
        if (!is_string($email) || !Validace::isEmail($email)) {
            $vady[] = 'email';
        }

        $role = $uzivatel['role'] ?? null;
        if (!is_string($role) || !isset(self::ROLE[$role])) {
            $vady[] = 'role';
        }

        return $vady;
    }

    /** Nová pozvánka: náhodný 64hex token a platnost do data v tvaru YYYY-MM-DD HH:MM:SS. */
    public static function pozvanka(): array
    {
        return [
            'token' => bin2hex(random_bytes(32)),
            'do' => date('Y-m-d H:i:s', time() + 7 * 86400),
        ];
    }

    /** Pozvánka platí, jen když má token a ještě neuplynulo datum platnosti. */
    public static function pozvankaPlati(array $pozvanka): bool
    {
        $token = $pozvanka['token'] ?? null;
        if (!is_string($token) || $token === '') {
            return false;
        }
        $do = $pozvanka['do'] ?? null;
        if (!is_string($do) || $do === '') {
            return false;
        }
        $konec = strtotime($do);
        if ($konec === false) {
            return false;
        }
        return $konec > time();
    }
}
