// =============================================================================
// Aura Skincare Voice Assistant Configuration
// =============================================================================

export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/**
 * Customer Care Phone Number Configuration.
 *
 * Keep this as a single clearly identifiable constant.
 * Default is a placeholder until the official company support line is provided.
 *
 * Examples of valid numbers when provisioned:
 *   "+911800123456" or "+918000000000"
 *
 * Current setting: PLACEHOLDER (Do not invent a real number).
 */
export const CUSTOMER_CARE_PHONE_NUMBER = "+918793016378";

/**
 * Check whether the configured phone number is a valid, callable number
 * suitable for initiating an active `tel:` link.
 * Rejects empty strings, placeholders containing 'X'/'x', and non-digit sequences.
 *
 * @param {string} phone
 * @returns {boolean}
 */
export function isValidPhoneNumber(phone) {
  if (!phone || typeof phone !== "string") return false;
  const trimmed = phone.trim();

  // Explicitly reject placeholders containing 'X' or 'x'
  if (/[xX]/.test(trimmed)) return false;

  // Extract numeric digits
  const digitsOnly = trimmed.replace(/\D/g, "");

  // International standard E.164 numbers typically contain between 7 and 15 digits
  return digitsOnly.length >= 7 && digitsOnly.length <= 15;
}

/**
 * Generates a clean `tel:` URI if the number is valid, or returns null.
 *
 * @param {string} phone
 * @returns {string|null}
 */
export function getTelLink(phone) {
  if (!isValidPhoneNumber(phone)) return null;
  const sanitized = phone.trim().replace(/[^\d+]/g, "");
  return `tel:${sanitized}`;
}
