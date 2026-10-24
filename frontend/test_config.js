import assert from "node:assert";
import {
  CUSTOMER_CARE_PHONE_NUMBER,
  isValidPhoneNumber,
  getTelLink,
} from "./src/config.js";

console.log("=================================================");
console.log("TESTING CUSTOMER CARE PHONE NUMBER CONFIGURATION");
console.log("=================================================");

// 1. Check default configured constant is present
assert(CUSTOMER_CARE_PHONE_NUMBER, "CUSTOMER_CARE_PHONE_NUMBER constant must be defined");
console.log("[PASS] Constant exists:", CUSTOMER_CARE_PHONE_NUMBER);

// 2. Default placeholder '+91XXXXXXXXXX' must be identified as placeholder (NOT valid for direct calling)
assert.strictEqual(
  isValidPhoneNumber(CUSTOMER_CARE_PHONE_NUMBER),
  false,
  "Placeholder '+91XXXXXXXXXX' must not be validated as a real callable number"
);
assert.strictEqual(
  getTelLink(CUSTOMER_CARE_PHONE_NUMBER),
  null,
  "Placeholder '+91XXXXXXXXXX' must return null for getTelLink to trigger friendly message"
);
console.log("[PASS] Placeholder '+91XXXXXXXXXX' rejected safely without generating broken tel link");

// 3. Other placeholder formats
assert.strictEqual(isValidPhoneNumber(""), false);
assert.strictEqual(isValidPhoneNumber(null), false);
assert.strictEqual(isValidPhoneNumber("123"), false);
assert.strictEqual(isValidPhoneNumber("XXXXXXXXXX"), false);
assert.strictEqual(isValidPhoneNumber("+1-800-XXX-XXXX"), false);
console.log("[PASS] Empty and invalid inputs rejected safely");

// 4. Test valid real phone numbers when configured
assert.strictEqual(isValidPhoneNumber("+911800123456"), true);
assert.strictEqual(getTelLink("+911800123456"), "tel:+911800123456");

assert.strictEqual(isValidPhoneNumber("+91 98765 43210"), true);
assert.strictEqual(getTelLink("+91 98765 43210"), "tel:+919876543210");

assert.strictEqual(isValidPhoneNumber("+1 (800) 555-0199"), true);
assert.strictEqual(getTelLink("+1 (800) 555-0199"), "tel:+18005550199");
console.log("[PASS] Valid numbers properly generate sanitized 'tel:' URIs");

console.log("=================================================");
console.log("ALL PHONE CONFIGURATION TESTS PASSED (100%)");
console.log("=================================================");
