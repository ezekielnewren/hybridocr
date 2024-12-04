use rustargon2::add_fdsa;

use wasm_bindgen_test::*;

// wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
pub fn test_add() {
    assert_eq!(add_fdsa(1, 2), 3);
}
