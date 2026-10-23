<?php
/* Fotka, která se do paměti nerozbalí. GD drží obrázek nekomprimovaný —
   4 bajty na pixel — takže 7000×7000 je skoro 200 MB a PHP na memory_limit
   umře fatální chybou. Tu nejde odchytit: zákazník dostane 500 a prázdnou
   odpověď. Proto se rozhoduje z hlavičky souboru a tahle výjimka říká „je to
   obrázek, jen moc velký". Router z ní dělá 413 a administrace poradí, aby se
   fotka zmenšila. */

declare(strict_types=1);

namespace App\Fotky;

final class MocVelka extends \RuntimeException
{
}
