pub mod util;

use argon2::{Algorithm};
use wasm_bindgen::prelude::*;

use crate::util::{PixelBuffer, Quadrilateral, _pt, argon2, Point};

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
pub fn perspective_transform(w: u32, h: u32, c: u8, interleaved: bool, data: Vec<u8>, _quad: Vec<f32>) -> Vec<u8> {
    let pb = PixelBuffer::new(w as usize, h as usize, c as usize, interleaved, data).unwrap();
    let quad = Quadrilateral{
        tl: Point{x: _quad[0], y: _quad[1] },
        tr: Point{x: _quad[2], y: _quad[3] },
        br: Point{x: _quad[4], y: _quad[5] },
        bl: Point{x: _quad[6], y: _quad[7] },
    };
    let result = _pt(pb, quad).unwrap();
    let mut out = Vec::<u8>::new();
    out.extend_from_slice(&(result.width as u32).to_le_bytes());
    out.extend_from_slice(&(result.height as u32).to_le_bytes());
    out.extend_from_slice(&(result.channels as u8).to_le_bytes());
    if result.interleaved {
        out.push(1u8);
    } else {
        out.push(0u8);
    }
    out.extend_from_slice(result.data.as_slice());
    out
}

