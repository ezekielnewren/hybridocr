use wasm_bindgen::JsValue;
use wasm_bindgen::prelude::wasm_bindgen;
use crate::util::{PixelBuffer, Quadrilateral, _pt};

pub mod util;


#[wasm_bindgen]
pub fn _argon2(alg: usize, password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> JsValue {
    match util::argon2(alg, password, salt, m, t, p, length) {
        Ok(v) => serde_wasm_bindgen::to_value(&v).unwrap(),
        Err(e) => serde_wasm_bindgen::to_value(&e).unwrap(),
    }
}


#[wasm_bindgen]
pub fn _perspective_transform(_image: JsValue, _quad: JsValue) -> JsValue {
    let image = serde_wasm_bindgen::from_value::<PixelBuffer>(_image).unwrap();
    let quad = serde_wasm_bindgen::from_value::<Quadrilateral>(_quad).unwrap();
    let result = _pt(image, quad);
    match result {
        Ok(v) => serde_wasm_bindgen::to_value(&v).unwrap(),
        Err(e) => serde_wasm_bindgen::to_value(&e).unwrap(),
    }
}
