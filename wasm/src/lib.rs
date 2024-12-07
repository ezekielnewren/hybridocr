pub mod util;

use argon2::{Algorithm};
use wasm_bindgen::prelude::*;

use image::{EncodableLayout};
use serde::{Serialize, Deserialize};
use crate::util::{PixelBuffer, Quadrilateral, _perspective_transform, argon2};

#[wasm_bindgen]
pub fn _argon2id(password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
    argon2(Algorithm::Argon2id, password, salt, m, t, p, length)
}


#[wasm_bindgen]
pub fn _argon2i(password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
    argon2(Algorithm::Argon2i, password, salt, m, t, p, length)
}


#[wasm_bindgen]
pub fn _argon2d(password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
    argon2(Algorithm::Argon2d, password, salt, m, t, p, length)
}



#[wasm_bindgen]
pub fn perspective_transform(_image: JsValue, _quad: JsValue) -> JsValue {
    let image = serde_wasm_bindgen::from_value::<PixelBuffer>(_image).unwrap();
    let quad = serde_wasm_bindgen::from_value::<Quadrilateral>(_quad).unwrap();
    let result = _perspective_transform(image, quad);
    match result {
        Ok(v) => serde_wasm_bindgen::to_value(&v).unwrap(),
        Err(e) => serde_wasm_bindgen::to_value(&e).unwrap(),
    }
}

