<?php
/* Zpráva se neodesílá, jen se připíše do souboru. Slouží na zkoušení
   (testovací běh) a jako záchrana, když na serveru není pošta. */

declare(strict_types=1);

namespace App\Posta;

final class PrepravkaLog implements Prepravka
{
    public function __construct(private readonly string $soubor)
    {
    }

    public function posli(string $komu, string $predmet, string $telo, array $hlavicky): bool
    {
        $zapis = '=== ' . date('Y-m-d H:i:s') . ' -> ' . $komu . "\n";
        foreach ($hlavicky as $jmeno => $hodnota) {
            $zapis .= $jmeno . ': ' . $hodnota . "\n";
        }
        $zapis .= 'Subject: ' . $predmet . "\n\n" . $telo . "\n\n";
        return file_put_contents($this->soubor, $zapis, FILE_APPEND | LOCK_EX) !== false;
    }
}
