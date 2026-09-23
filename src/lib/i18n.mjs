/**
 * C-002: Slovníky překladů – tečkové klíče, záskok, zplošťování
 */

/**
 * Resolve a dotted path in a nested object.
 * Returns the value at the path, or null if any intermediate key is missing
 * or not an object (except the final value which can be anything).
 */
export function get(dict, path) {
  if (dict == null || typeof dict !== 'object' || Array.isArray(dict)) return null;
  const parts = path.split('.');
  let current = dict;
  for (let i = 0; i < parts.length; i++) {
    const key = parts[i];
    if (current == null || typeof current !== 'object' || Array.isArray(current)) return null;
    if (!(key in current)) return null;
    current = current[key];
  }
  return current;
}

/**
 * Translate: look up `path` in `dict`, fall back to `fallbackDict`, then to `path` itself.
 * Substitute {key} placeholders from `vars`.
 */
export function t(dict, path, vars = {}, fallbackDict = null) {
  let value = get(dict, path);
  if (value != null && typeof value === 'string' && value.trim() !== '') {
    // use it
  } else if (fallbackDict != null) {
    value = get(fallbackDict, path);
    if (value != null && typeof value === 'string' && value.trim() !== '') {
      // use it
    } else {
      value = null;
    }
  } else {
    value = null;
  }

  if (value == null || typeof value !== 'string') {
    value = path;
  }

  // Substitute {key} placeholders
  return value.replace(/\{([^}]+)\}/g, (_match, key) => {
    if (key in vars) return String(vars[key]);
    return _match;
  });
}

/**
 * Flatten a nested object into dot-notation keys.
 * Arrays are indexed by number. Only leaf values appear in the result.
 */
export function flatten(obj, prefix = '') {
  const result = {};
  _flatten(obj, prefix, result);
  return result;
}

function _flatten(obj, prefix, result) {
  if (obj == null || typeof obj !== 'object') return;

  if (Array.isArray(obj)) {
    for (let i = 0; i < obj.length; i++) {
      const key = prefix ? prefix + '.' + i : String(i);
      const val = obj[i];
      if (val != null && typeof val === 'object' && !Array.isArray(val)) {
        _flatten(val, key, result);
      } else if (val != null && typeof val === 'object' && Array.isArray(val)) {
        _flatten(val, key, result);
      } else {
        result[key] = val;
      }
    }
  } else {
    const keys = Object.keys(obj);
    for (const key of keys) {
      const fullKey = prefix ? prefix + '.' + key : key;
      const val = obj[key];
      if (val != null && typeof val === 'object' && !Array.isArray(val)) {
        _flatten(val, fullKey, result);
      } else if (val != null && typeof val === 'object' && Array.isArray(val)) {
        _flatten(val, fullKey, result);
      } else {
        result[fullKey] = val;
      }
    }
  }
}

/**
 * Unflatten a dot-notation map back into a nested object.
 * Segments that are non-negative integers create arrays.
 */
export function unflatten(map) {
  const root = {};
  for (const key of Object.keys(map)) {
    const parts = key.split('.');
    let current = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      const isNum = /^\d+$/.test(part);

      if (isLast) {
        current[part] = map[key];
      } else {
        const nextPart = parts[i + 1];
        const nextIsNum = /^\d+$/.test(nextPart);

        if (isNum) {
          // Ensure array exists
          if (!Array.isArray(current)) {
            // Convert object to array if needed
            const arr = [];
            for (const k of Object.keys(current)) {
              const nk = Number(k);
              if (Number.isInteger(nk) && nk >= 0) {
                arr[nk] = current[k];
              } else {
                arr[k] = current[k];
              }
            }
            current = arr;
          }
          const idx = Number(part);
          if (current[idx] === undefined) {
            // Decide: array or object for next level
            if (nextIsNum) {
              current[idx] = [];
            } else {
              current[idx] = {};
            }
          }
          current = current[idx];
        } else {
          if (current[part] === undefined) {
            if (nextIsNum) {
              current[part] = [];
            } else {
              current[part] = {};
            }
          }
          current = current[part];
        }
      }
    }
  }
  return root;
}

/**
 * Find keys present in `reference` (with non-empty trimmed string values)
 * but missing or empty in `dict`.
 */
export function missingKeys(reference, dict) {
  const flatRef = flatten(reference);
  const result = [];
  for (const key of Object.keys(flatRef)) {
    const refVal = flatRef[key];
    // Only report if reference has a non-empty trimmed string
    if (typeof refVal === 'string' && refVal.trim() !== '') {
      const dictVal = get(dict, key);
      if (dictVal == null || (typeof dictVal === 'string' && dictVal.trim() === '')) {
        result.push(key);
      }
    }
  }
  return result;
}
