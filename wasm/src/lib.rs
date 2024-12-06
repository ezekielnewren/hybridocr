use argon2::{Algorithm, Argon2, Params, Version};
use wasm_bindgen::prelude::*;

use image::{EncodableLayout, GrayImage, Luma};
use imageproc::geometric_transformations::{warp, Interpolation, Projection};

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


#[wasm_bindgen]
struct PixelBuffer {
    pub width: u32,
    pub height: u32,
    pub channels: u8,
    pub interleaved: bool,
}

impl Clone for PixelBuffer {
    fn clone(&self) -> Self {
        Self {
            width: self.width,
            height: self.height,
            channels: self.channels,
            interleaved: self.interleaved,
        }
    }
}

impl Copy for PixelBuffer {

}

impl PixelBuffer {

    pub fn new(width: u32, height: u32, channels: u8, interleaved: bool) -> Self {
        Self {width, height, channels, interleaved}
    }

    pub fn as_channels(&self, src: Vec<u8>) -> Result<Vec<GrayImage>, String> {
        let mut dst: Vec<GrayImage> = Vec::new();
        let size: usize = (self.width*self.height) as usize;
        let channel_size = size/self.channels as usize;
        let r = size%self.channels as usize;
        if r != 0 {
            return Err(String::from("image size is not an integer multiple of channels"));
        }
        if self.interleaved {
            for channel in 0usize..self.channels as usize {
                let mut t = Vec::<u8>::new();
                for pixel in 0..channel_size {
                    t.push(src[pixel*self.channels as usize+channel]);
                }
                dst.push(GrayImage::from_vec(self.width, self.height, t).unwrap());
            }
        } else {
            dst = Vec::new();
            for channel in 0usize..self.channels as usize {
                let off = channel*channel_size;
                let v = Vec::from(&src[off..off+channel_size]);
                let img = GrayImage::from_vec(self.width, self.height, v).unwrap();
                dst.push(img);
            }
        }
        Ok(dst)
    }

    pub fn from_channels(image: Vec<GrayImage>, interleave: bool) -> Result<(Self, Vec<u8>), String> {
        let channels = image.len();
        let width = image[0].width() as usize;
        let height = image[0].height() as usize;
        for i in 1..image.len() {
            if image[i].width() as usize != width {
                return Err(String::from("image width of all channels must be the same"));
            }
            if image[i].height() as usize != height {
                return Err(String::from("image height of all channels must be the same"));
            }
        }

        let mut dst: Vec<u8>;
        if interleave {
            let size: usize = width*height;
            dst = vec![0u8; size];
            let channel_size = size/channels;
            let r = size%channels;
            if r != 0 {
                return Err(String::from("image size is not an integer multiple of channels"));
            }
            for channel in 0usize..channels {
                let t = image[channel].as_bytes();
                for pixel in 0..channel_size {
                    dst[pixel*channels+channel] = t[pixel];
                }
            }
        } else {
            dst = Vec::new();
            for channel in 0usize..channels {
                dst.copy_from_slice(image[channel].as_bytes());
            }
        }
        Ok((Self {
            width: width as u32,
            height: height as u32,
            channels: channels as u8,
            interleaved: interleave,
        }, dst))
    }
}

pub fn midpoint(a: (f32, f32), b: (f32, f32)) -> (f32, f32) {
    ((a.0+b.0)/2.0, (a.1+b.1)/2.0)
}

pub fn distance(a: (f32, f32), b: (f32, f32)) -> f32 {
    ((a.0-b.0).powi(2) + (a.1-b.1).powi(2)).sqrt()
}


// #[wasm_bindgen]
pub fn pertrans(image: PixelBuffer, data: Vec<u8>, src_points: [(f32, f32); 4]) -> Result<(PixelBuffer, Vec<u8>), String> {
    let warp = perspective_transform(image, data, src_points)?;
    Ok(warp)
}


pub fn perspective_transform(
    image: PixelBuffer,
    src: Vec<u8>,
    src_points: [(f32, f32); 4],
) -> Result<(PixelBuffer, Vec<u8>), String> {
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
    let interleaved = image.interleaved;
    let projection = Projection::from_control_points(src_points, dst_points).unwrap();
    let default = Luma::from([0u8]);
    let mut output = Vec::<GrayImage>::new();
    for img in image.as_channels(src)? {
        let warped_image = warp(
            &img,
            &projection,
            Interpolation::Bicubic,
            default,
        );
        output.push(warped_image);
    }
    PixelBuffer::from_channels(output, interleaved)
}
