use argon2::{Algorithm, Argon2, Params, Version};
use wasm_bindgen::prelude::*;

use image::{DynamicImage, EncodableLayout, GrayImage, ImageBuffer, Luma};
use image::DynamicImage::ImageLuma8;
use imageproc::geometric_transformations::{warp, Interpolation, Projection};
use serde::{Serialize, Deserialize};

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


pub fn argon2(alg: Algorithm, password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
    let inst = Argon2::new(alg, Version::V0x13, Params::new(m, t, p, Some(length as usize)).unwrap());
    let mut buff = vec![0u8; length as usize];
    inst.hash_password_into(password, salt, &mut buff).expect("hashing failed");
    buff
}


#[derive(Serialize, Deserialize)]
pub struct Point {
    pub x: f32,
    pub y: f32,
}

impl Clone for Point {
    fn clone(&self) -> Self {
        Self{ x: self.x, y: self.y }
    }
}

impl Copy for Point {}


pub fn midpoint(a: Point, b: Point) -> Point {
    Point{x: (a.x+b.x)/2.0, y: (a.y+b.y)/2.0}
}

pub fn distance(a: Point, b: Point) -> f32 {
    ((a.x-b.x).powi(2) + (a.y-b.y).powi(2)).sqrt()
}


pub fn deinterleave(src: &Vec<u8>, channels: u8) -> Result<Vec<u8>, String> {
    let channel_size = src.len() / channels as usize;
    let r = src.len() % channels as usize;
    if r != 0 {
        return Err(String::from("image size is not an integer multiple of channels"));
    }
    let mut dst = vec![0u8; src.len()];
    for channel in 0..channels as usize {
        for pixel in 0..channel_size {
            dst[channel*channel_size+pixel] = src[pixel*channels as usize+channel];
        }
    }
    Ok(dst)
}

pub fn interleave(src: &[u8], channels: u8) -> Result<Vec<u8>, String> {
    let channel_size = src.len() / channels as usize;
    let r = src.len() % channels as usize;
    if r != 0 {
        return Err(String::from("image size is not an integer multiple of channels"));
    }
    let mut dst = vec![0u8; src.len()];
    for channel in 0..channels as usize {
        for pixel in 0..channel_size {
            dst[pixel*channels as usize+channel] = src[channel*channel_size+pixel];
        }
    }
    Ok(dst)
}


#[derive(Serialize, Deserialize)]
pub struct PixelBuffer {
    pub width: u32,
    pub height: u32,
    pub channels: u8,
    pub interleaved: bool,
    pub data: Vec<u8>,
}


impl PixelBuffer {
    pub fn as_channels(&self) -> Result<Vec<GrayImage>, String> {
        let mut dst: Vec<GrayImage> = Vec::new();
        let channel_size = self.data.len()/self.channels as usize;
        let t: Vec<u8>;
        let planar: &[u8];
        if self.interleaved {
            t = deinterleave(&self.data, self.channels)?;
            planar = t.as_slice();
        } else {
            planar = self.data.as_slice();
        }
        for channel in 0usize..self.channels as usize {
            let off = channel*channel_size;
            let pixel_data: Vec<u8> = Vec::from(&planar[off..off+channel_size]);
            assert_eq!(self.width*self.height, pixel_data.len() as u32);
            let img: GrayImage = GrayImage::from_vec(self.width, self.height, pixel_data).unwrap();
            dst.push(img);
        }
        Ok(dst)
    }

    pub fn as_dynamic_image(&self) -> Result<DynamicImage, String> {
        let t: Vec<u8>;
        let planar: &[u8];
        if self.interleaved {
            t = deinterleave(&self.data, self.channels)?;
            planar = t.as_slice();
        } else {
            planar = self.data.as_slice();
        }

        if self.channels == 1 {
            Ok(DynamicImage::ImageLuma8(ImageBuffer::from_vec(self.width, self.height, planar.to_vec()).unwrap()))
        } else if self.channels == 3 {
            Ok(DynamicImage::ImageRgb8(ImageBuffer::from_vec(self.width, self.height, planar.to_vec()).unwrap()))
        } else if self.channels == 4 {
            Ok(DynamicImage::ImageRgba8(ImageBuffer::from_vec(self.width, self.height, planar.to_owned()).unwrap()))
        } else {
            Err(String::from("Illegal parameters"))
        }
    }

    pub fn from_channels(channel: &Vec<GrayImage>, interleaved: bool) -> Result<Self, String> {
        let width = channel[0].width() as usize;
        let height = channel[0].height() as usize;
        for i in 1..channel.len() {
            if channel[i].width() as usize != width {
                return Err(String::from("image width of all channels must be the same"));
            }
            if channel[i].height() as usize != height {
                return Err(String::from("image height of all channels must be the same"));
            }
        }

        let mut dst: Vec<u8>;
        if interleaved {
            let mut src = Vec::<u8>::new();
            for c in channel {
                src.extend_from_slice(c.as_bytes());
            }
            dst = interleave(src.as_slice(), channel.len() as u8)?;
        } else {
            dst = Vec::new();
            for c in channel {
                dst.extend_from_slice(c.as_bytes());
            }
        }
        Ok(Self {
            width: width as u32,
            height: height as u32,
            channels: channel.len() as u8,
            interleaved,
            data: dst
        })
    }
}


#[derive(Serialize, Deserialize)]
pub struct Quadrilateral {
    pub tl: Point,
    pub tr: Point,
    pub br: Point,
    pub bl: Point,
}


impl Quadrilateral {
    pub fn as_array(&self) -> [(f32, f32); 4] {
        [(self.tl.x, self.tl.y), (self.tr.x, self.tr.y), (self.br.x, self.br.y), (self.bl.x, self.bl.y)]
    }

    pub fn dst_rect(&self) -> [(f32, f32); 4] {
        let left_mid = midpoint(self.tl, self.bl);
        let right_mid = midpoint(self.tr, self.br);
        let width = distance(left_mid, right_mid);

        let top_mid = midpoint(self.tl, self.tr);
        let bot_mid = midpoint(self.bl, self.br);
        let height = distance(top_mid, bot_mid);

        [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)]
    }
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


pub fn _perspective_transform(image: PixelBuffer, quad: Quadrilateral) -> Result<PixelBuffer, String> {
    let projection = Projection::from_control_points(quad.as_array(), quad.dst_rect()).unwrap();
    let mut output = Vec::<GrayImage>::new();
    for img in image.as_channels()? {
        let warped_image = warp(
            &img,
            &projection,
            Interpolation::Bicubic,
            Luma::from([0u8]),
        );
        output.push(warped_image);
    }
    PixelBuffer::from_channels(&output, image.interleaved)
}