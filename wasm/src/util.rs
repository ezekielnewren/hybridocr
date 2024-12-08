use argon2::{Algorithm, Argon2, Params, Version};
use image::{DynamicImage, EncodableLayout, GrayImage, ImageBuffer, Luma, Rgb, RgbImage, Rgba, RgbaImage};
use imageproc::drawing::Canvas;
use imageproc::geometric_transformations::{warp_into, Interpolation, Projection};
use serde::{Deserialize, Serialize};


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


pub fn transpose(src: &[u8], width: usize, height: usize, dst: &mut [u8]) -> Result<(), String> {
    if src.len() != dst.len() {
        return Err(String::from("src and dst length must be the same"));
    }
    if width*height != src.len() {
        return Err(String::from("the length of src must equal width*height"));
    }
    if width == 1 || height == 1 {
        dst.copy_from_slice(&src);
        return Ok(());
    }

    for col in 0..width {
        for row in 0..height {
            let s = row*width+col;
            let d = col*height+row;
            dst[d] = src[s];
        }
    }

    Ok(())
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

    pub fn new(width: u32, height: u32, channels: u8, interleaved: bool, src: &[u8]) -> Result<Self, String> {
        if width*height*channels as u32 != src.len() as u32 {
            return Err(String::from("width*height*channels must equal src.len()"));
        }

        Ok(Self {
            width,
            height,
            channels,
            interleaved,
            data: src.to_vec(),
        })
    }

    pub fn from_dynamic_image(img: &DynamicImage) -> Self {
        Self::new(
            img.width(),
            img.height(),
            img.color().channel_count(),
            true,
            img.as_bytes()
        ).unwrap()
    }

    pub fn toggle_interleaved(&mut self) {
        let mut w = self.channels as usize;
        let mut h = (self.width*self.height) as usize;
        if !self.interleaved {
            (w, h) = (h, w);
        }

        let mut src = self.data.clone();
        transpose(src.as_slice(), w, h, self.data.as_mut_slice()).unwrap();
        self.interleaved = !self.interleaved;
    }

    pub fn as_bytes(&self) -> Vec<u8> {
        if self.interleaved {
            self.data.clone()
        } else {
            let mut t = vec![0u8; self.data.len()];
            let w = (self.width * self.height) as usize;
            let h = self.channels as usize;
            transpose(self.data.as_slice(), w, h, t.as_mut_slice()).unwrap();
            t
        }
    }

    pub fn as_dynamic_image(&self) -> Result<DynamicImage, String> {
        let woven = self.as_bytes();

        if self.channels == 1 {
            Ok(DynamicImage::ImageLuma8(ImageBuffer::from_vec(self.width, self.height, woven).unwrap()))
        } else if self.channels == 2 {
            Ok(DynamicImage::ImageLumaA8(ImageBuffer::from_vec(self.width, self.height, woven).unwrap()))
        } else if self.channels == 3 {
            Ok(DynamicImage::ImageRgb8(ImageBuffer::from_vec(self.width, self.height, woven).unwrap()))
        } else if self.channels == 4 {
            Ok(DynamicImage::ImageRgba8(ImageBuffer::from_vec(self.width, self.height, woven).unwrap()))
        } else {
            Err(String::from("Illegal parameters"))
        }
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

    pub fn output_dimension(&self) -> (f32, f32) {
        let left_mid = midpoint(self.tl, self.bl);
        let right_mid = midpoint(self.tr, self.br);
        let width = distance(left_mid, right_mid);

        let top_mid = midpoint(self.tl, self.tr);
        let bot_mid = midpoint(self.bl, self.br);
        let height = distance(top_mid, bot_mid);

        (width, height)
    }

    pub fn dst_rect(&self) -> [(f32, f32); 4] {
        let (width, height) = self.output_dimension();

        [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)]
    }
}

pub fn _perspective_transform(pb: &PixelBuffer, quad: &Quadrilateral) -> Result<PixelBuffer, String> {
    let projection = Projection::from_control_points(quad.as_array(), quad.dst_rect()).unwrap();
    let out_dim = quad.output_dimension();
    let w = out_dim.0 as u32;
    let h = out_dim.1 as u32;

    let src = pb.as_bytes();
    let out_img: DynamicImage;
    if pb.channels == 1 {
        let gray = GrayImage::from_vec(pb.width, pb.height, src).unwrap();
        let dp = Luma([0]);
        let mut t = ImageBuffer::from_pixel(w, h, dp);
        warp_into(
            &gray,
            &projection,
            Interpolation::Bicubic,
            dp,
            &mut t,
        );
        out_img = DynamicImage::from(t);
    } else if pb.channels == 3 {
        let rgb = RgbImage::from_vec(pb.width, pb.height, src).unwrap();
        let dp = Rgb([0, 0, 0]);
        let mut t = ImageBuffer::from_pixel(w, h, dp);
        warp_into(
            &rgb,
            &projection,
            Interpolation::Bicubic,
            dp,
            &mut t,
        );
        out_img = DynamicImage::from(t);
    } else if pb.channels == 4 {
        let rgba = RgbaImage::from_vec(pb.width, pb.height, src).unwrap();
        let dp = Rgba([0u8, 0u8, 0u8, 0u8]);
        let mut t = ImageBuffer::from_pixel(w, h, dp);
        warp_into(
            &rgba,
            &projection,
            Interpolation::Bicubic,
            dp,
            &mut t,
        );
        out_img = DynamicImage::from(t);
    } else {
        return Err(String::from("only 1, 3, or 4 channels are supported"));
    }

    let mut pb_out = PixelBuffer::from_dynamic_image(&out_img);
    if !pb.interleaved {
        pb_out.toggle_interleaved();
    }
    Ok(pb_out)
}

