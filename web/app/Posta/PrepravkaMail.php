<?php
/* Odeslání přes mail() — tedy přes MTA, který na serveru běží. Na Debianu
   to obvykle znamená mít nainstalovaný a nastavený sendmail/postfix; když
   tam není, vrací mail() false a web to uživateli řekne. */

declare(strict_types=1);

namespace App\Posta;

final class PrepravkaMail implements Prepravka
{
    public function posli(string $komu, string $predmet, string $telo, array $hlavicky): bool
    {
        $radky = [];
        foreach ($hlavicky as $jmeno => $hodnota) {
            $radky[] = $jmeno . ': ' . $hodnota;
        }
        return mail($komu, $predmet, $telo, implode("\r\n", $radky));
    }
}
