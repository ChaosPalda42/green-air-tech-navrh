<?php

namespace App\Obsah;

final class I18n
{
    /**
     * Hodnota na tečkami oddělené cestě ('nav.sluzby'). Když kterýkoli krok neexistuje
     * nebo není pole, vrátí null. Prázdná cesta vrátí null.
     */
    public static function get(?array $dict, string $cesta): mixed
    {
        if ($cesta === '') {
            return null;
        }

        $parts = explode('.', $cesta);
        $current = $dict;

        foreach ($parts as $part) {
            if (!is_array($current) || !array_key_exists($part, $current)) {
                return null;
            }
            $current = $current[$part];
        }

        return $current;
    }

    /**
     * Přeložený text. Když v $dict chybí nebo není řetězec, zkusí $zaskok; když chybí
     * i tam, vrátí samotnou cestu. Zástupné {klic} nahradí hodnotou z $vars; zástupné,
     * pro které ve $vars nic není, zůstane v textu tak, jak je.
     */
    public static function t(?array $dict, string $cesta, array $vars = [], ?array $zaskok = null): string
    {
        $val = self::get($dict, $cesta);

        if (!is_string($val)) {
            if ($zaskok !== null) {
                $val = self::get($zaskok, $cesta);
            }
            
            if (!is_string($val)) {
                return $cesta;
            }
        }

        foreach ($vars as $key => $value) {
            $val = str_replace('{' . $key . '}', (string)$value, $val);
        }

        return $val;
    }

    /**
     * Vnořená pole -> jedna úroveň s tečkovanými klíči. Pořadí klíčů se zachová
     * (průchod do hloubky v pořadí, v jakém klíče leží).
     */
    public static function flatten(array $obj, string $prefix = ''): array
    {
        $result = [];
        foreach ($obj as $key => $value) {
            $newKey = $prefix === '' ? (string)$key : $prefix . '.' . $key;
            if (is_array($value) && !empty($value)) {
                $result = array_merge($result, self::flatten($value, $newKey));
            } else {
                $result[$newKey] = $value;
            }
        }
        return $result;
    }

    /**
     * Opak flatten.
     */
    public static function unflatten(array $mapa): array
    {
        $result = [];
        foreach ($mapa as $key => $value) {
            $parts = explode('.', $key);
            $current = &$result;
            foreach ($parts as $part) {
                if (!isset($current[$part]) || !is_array($current[$part])) {
                    $current[$part] = [];
                }
                $current = &$current[$part];
            }
            $current = $value;
        }
        return $result;
    }

    /**
     * Seznam tečkovaných klíčů, které jsou ve $vzor a ve $dict chybí nebo jsou prázdný
     * řetězec. Pořadí jako ve vzoru.
     */
    public static function missingKeys(array $vzor, array $dict): array
    {
        $missing = [];
        $flattenedVzor = self::flatten($vzor);
        
        foreach ($flattenedVzor as $key => $value) {
            $dictVal = self::get($dict, $key);
            if ($dictVal === null || $dictVal === '') {
                $missing[] = $key;
            }
        }
        
        return $missing;
    }
}
