use argon2::{Algorithm, Argon2, Params, Version};
use wasm_bindgen::prelude::*;

use image::{DynamicImage, GrayImage, ImageBuffer, Luma, Rgb, RgbImage, Rgba, RgbaImage};
use imageproc::definitions::Image;
use imageproc::geometric_transformations::{warp, Interpolation, Projection};
use webp::{Decoder, Encoder};

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


// #[wasm_bindgen]
struct PixelBuffer {
    pub width: u32,
    pub height: u32,
    pub channels: u8,
    pub interleaved: bool,
    pub data: Vec<u8>,
}

impl PixelBuffer {
    pub fn new(width: u32, height: u32, channels: u8, interleaved: bool, data: Vec<u8>) -> Self {
        Self {width, height, channels, interleaved, data}
    }

    pub fn to_dynamic_image(&self) -> Result<DynamicImage, String> {
        let mut dst: Vec<u8>;
        if self.interleaved {
            let size: usize = (self.width*self.height) as usize;
            dst = vec![0u8; size];
            let channel_size = size/self.channels as usize;
            let r = size%self.channels as usize;
            if r != 0 {
                return Err(String::from("image size is not an integer multiple of channels"));
            }
            for pixel in 0..channel_size {
                for channel in 0usize..self.channels as usize {
                    dst[channel*channel_size+pixel] = self.data[pixel*self.channels as usize+channel];
                }
            }
        } else {
            dst = self.data.clone();
        }
        if self.channels == 1 {
            Ok(DynamicImage::ImageLuma8(ImageBuffer::from_vec(self.width, self.height, dst).unwrap()))
        } else if self.channels == 3 {
            Ok(DynamicImage::ImageRgb8(ImageBuffer::from_vec(self.width, self.height, dst).unwrap()))
        } else if self.channels == 4 {
            Ok(DynamicImage::ImageRgba8(ImageBuffer::from_vec(self.width, self.height, dst).unwrap()))
        } else {
            Err(String::from("Illegal parameters"))
        }
    }

    pub fn from_dynamic_image(image: &DynamicImage, interleave: bool) -> Result<Self, String> {
        let channels = image.color().channel_count();
        let src = image.as_bytes();
        let mut dst: Vec<u8>;
        if interleave {
            let size: usize = (image.width()*image.height()) as usize;
            dst = vec![0u8; size];
            let channel_size = size/channels as usize;
            let r = size%channels as usize;
            if r != 0 {
                return Err(String::from("image size is not an integer multiple of channels"));
            }
            for pixel in 0..channel_size {
                for channel in 0usize..channels as usize {
                    dst[pixel*channels as usize+channel] = src[channel*channel_size+pixel];
                }
            }
        } else {
            dst = Vec::from(src);
        }
        Ok(Self {
            width: image.width(),
            height: image.height(),
            channels,
            interleaved: interleave,
            data: dst
        })
    }
}

pub fn midpoint(a: (f32, f32), b: (f32, f32)) -> (f32, f32) {
    ((a.0+b.0)/2.0, (a.1+b.1)/2.0)
}

pub fn distance(a: (f32, f32), b: (f32, f32)) -> f32 {
    ((a.0-b.0).powi(2) + (a.1-b.1).powi(2)).sqrt()
}

// #[wasm_bindgen]
pub fn perspective_transform(
    image: PixelBuffer,
    src_points: [(f32, f32); 4],
) -> Result<PixelBuffer, String> {
    let tl = src_points[0];
    let tr = src_points[1];
    let br = src_points[2];
    let bl = src_points[3];

    let left_mid = midpoint(tl, bl);
    let right_mid = midpoint(tr, br);
    let width = distance(left_mid, right_mid);

    let top_mid = midpoint(tl, tr);
    let bot_mid = midpoint(bl, br);
    let height = distance(top_mid, bot_mid);


    // Define destination points as a rectangle
    let dst_points = [
        (0.0, 0.0),
        (width, 0.0),
        (width, height),
        (0.0, height),
    ];

    // Compute the perspective projection
    let projection = Projection::from_control_points(src_points, dst_points).unwrap();
    let img = image.to_dynamic_image()?;


    let default_pixel: Rgba<u8> = Rgba::from([0u8; 1]);
    let x: Image<Rgba<u8>> = RgbaImage::from_pixel(1, 1, default_pixel);

    let warped_image = warp(
        &img.to_rgba8(),
        &projection,
        Interpolation::Bicubic,
        default_pixel,
    );
    let output = PixelBuffer::from_dynamic_image(&warped_image, image.interleaved)?;

    // let di = DynamicImage::from(warped_image);
    // let encoder = Encoder::from_image(&di)?;
    // let webp_binary = encoder.encode(75.0).to_vec();

    Ok(output)
}
