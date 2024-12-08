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

}

impl PixelBuffer {
    pub fn as_channels(&self) -> Result<Vec<GrayImage>, String> {
        let mut dst: Vec<GrayImage> = Vec::new();
        let channel_size = self.data.len()/self.channels as usize;
        let mut t: Vec<u8>;
        let planar: &[u8];
        if self.interleaved {
            t = vec![0u8; self.data.len()];
            transpose(self.data.as_slice(), self.channels as usize, channel_size, t.as_mut_slice())?;
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

    pub fn from_dynamic_image(img: &DynamicImage) -> Self {
        Self {
            width: img.width(),
            height: img.height(),
            channels: img.color().channel_count(),
            interleaved: false,
            data: Vec::from(img.as_bytes()),
        }
    }

    pub fn as_dynamic_image(&self) -> Result<DynamicImage, String> {
        let mut t: Vec<u8>;
        let planar: &[u8];
        if self.interleaved {
            t = vec![0u8; self.data.len()];
            transpose(self.data.as_slice(), self.channels as usize, (self.width*self.height) as usize, t.as_mut_slice())?;
            planar = t.as_slice();
        } else {
            planar = self.data.as_slice();
        }

        if self.channels == 1 {
            Ok(DynamicImage::ImageLuma8(ImageBuffer::from_vec(self.width, self.height, planar.to_vec()).unwrap()))
        } else if self.channels == 2 {
            Ok(DynamicImage::ImageLumaA8(ImageBuffer::from_vec(self.width, self.height, planar.to_vec()).unwrap()))
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
            dst = vec![0u8; src.len()];
            transpose(src.as_slice(), width*height, channel.len(), dst.as_mut_slice())?;
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

pub fn _perspective_transform(pb: PixelBuffer, quad: Quadrilateral) -> Result<PixelBuffer, String> {
    let projection = Projection::from_control_points(quad.as_array(), quad.dst_rect()).unwrap();
    let out_dim = quad.output_dimension();
    let w = out_dim.0 as u32;
    let h = out_dim.1 as u32;
    let mut output = Vec::<GrayImage>::new();

    let out_img: DynamicImage;
    if pb.channels == 1 {
        let gray = GrayImage::from_vec(pb.width, pb.height, pb.data).unwrap();
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
        let rgb = RgbImage::from_vec(pb.width, pb.height, pb.data).unwrap();
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
        let rgba = RgbaImage::from_vec(pb.width, pb.height, pb.data).unwrap();
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

    Ok(PixelBuffer::from_dynamic_image(&out_img))
}

