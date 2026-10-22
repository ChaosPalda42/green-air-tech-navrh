<?php
/* Čím se zpráva odešle. Na ostrém webu PrepravkaMail (funkce mail(), MTA
   serveru) nebo PrepravkaSmtp; v testu a při zkoušení PrepravkaLog, která
   zprávu jen zapíše do souboru. */

declare(strict_types=1);

namespace App\Posta;

interface Prepravka
{
    /** @param array<string,string> $hlavicky */
    public function posli(string $komu, string $predmet, string $telo, array $hlavicky): bool;
}
