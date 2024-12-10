use argon2::{Algorithm, Argon2, Params, Version};
use image::{DynamicImage, GrayImage, ImageBuffer, Luma, Rgb, RgbImage, Rgba, RgbaImage};
use imageproc::geometric_transformations::{warp_into, Interpolation, Projection};
use serde::{Deserialize, Serialize};


pub fn argon2(alg: Algorithm, password: &[u8], salt: &[u8], m: u32, t: u32, p: u32, length: u32) -> Vec<u8> {
    let inst = Argon2::new(alg, Version::V0x13, Params::new(m, t, p, Some(length as usize)).unwrap());
    let mut buff = vec![0u8; length as usize];
    inst.hash_password_into(password, salt, &mut buff).expect("hashing failed");
    buff
}

pub enum Interp {
    Nearest = 0isize,
    Bilinear = 1isize,
    Biquadratic = 2isize,
    Bicubic = 3isize,
    Lanczos4x4 = 4isize,
    Lanczos6x6 = 5isize,
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

    pub fn blank(width: u32, height: u32, channels: u8, interleaved: bool) -> Self {
        Self {
            width,
            height,
            channels,
            interleaved,
            data: vec![0u8; (width*height*channels as u32) as usize],
        }
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

        let src = self.data.clone();
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


    pub fn in_bounds(&self, x: f32, y: f32, c: u8) -> bool {
        let (w, h) = (self.width as f32, self.height as f32);
        0.0 <= x && x < w && 0.0 <= y && y < h && c < self.channels
    }

    pub fn get(&self, mut _x: f32, mut _y: f32, c: u8, closest: bool) -> u8 {
        if !self.in_bounds(_x, _y, c) {
            if closest {
                if _x < 0.0 {
                    _x = 0.0;
                } else if _x >= self.width as f32 {
                    _x = self.width as f32-1.0;
                }
                if _y < 0.0 {
                    _y = 0.0;
                } else if _y >= self.height as f32 {
                    _y = self.height as f32-1.0;
                }
            } else {
                return 0u8;
            }
        }
        let (w, h) = (self.width as usize, self.height as usize);
        let (x, y) = (_x as usize, _y as usize);
        if self.interleaved {
            let pixel_size = self.channels as usize;
            self.data[y*pixel_size*w + x*pixel_size + c as usize]
        } else {
            let channel_size = w*h;
            self.data[c as usize*channel_size + y*w + x]
        }
    }

    pub fn at_mut(&mut self, x: usize, y: usize, c: u8) -> &mut u8 {
        if !self.in_bounds(x as f32, y as f32, c) {
            panic!("Index out of bounds: x={}, y={}, c={}", x, y, c);
        }
        let (w, h) = (self.width as usize, self.height as usize);
        if self.interleaved {
            let pixel_size = self.channels as usize;
            &mut self.data[y*pixel_size*w + x*pixel_size + c as usize]
        } else {
            let channel_size = w*h;
            &mut self.data[c as usize*channel_size + y*w + x]
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


pub fn get_transform(proj: &Projection) -> [f32; 9] {
    unsafe {
        let ptr = proj as *const Projection;
        let x = ptr as *const [f32; 9];
        *x.add(1)
    }
}


pub fn weight_linear(span: &[u8], w: f32) -> u8 {
    #[cfg(debug_assertions)]
    {
        if span.len() != 2 {
            panic!("must have exactly 2 elements");
        }
        if !(0.0 <= w && w <= 1.0) {
            panic!("weight must be between 0.0 and 1.0");
        }
    }
    let a = span[0] as f32;
    let b = span[1] as f32;

    (a+(b-a)*w) as u8
}

pub fn blend_linear(src: &PixelBuffer, x: f32, y: f32, c: u8) -> u8 {
    let top = [
        src.get(x-1.0, y-1.0, c, true),
        src.get(x, y-1.0, c, true),
    ];
    let bot = [
        src.get(x, y, c, true),
        src.get(x-1.0, y, c, true),
    ];
    let w = x-x.floor();
    let col = [
        weight_linear(&top, w),
        weight_linear(&bot, w),
    ];
    weight_linear(&col, y-y.floor())
}


pub fn weight_quadratic(span: &[u8], w: f32) -> u8 {
    #[cfg(debug_assertions)]
    {
        if span.len() != 3 {
            panic!("must have exactly 3 elements");
        }
        if !(0.0 <= w && w <= 1.0) {
            panic!("weight must be between 0.0 and 1.0");
        }
    }

    let p0 = span[0] as f32;
    let p1 = span[1] as f32;
    let p2 = span[2] as f32;

    let a = 2.0*p2 - 4.0*p1 + 2.0*p0;
    let b = -p2 + 4.0*p1 - 3.0*p0;
    let c = p0;

    let result = a*w*w + b*w + c;

    result.clamp(0.0, 255.0) as u8
}


pub fn blend_quadratic(src: &PixelBuffer, x: f32, y: f32, c: u8) -> u8 {
    let mut t = [0u8; 3];
    for rowi in 0..3 {
        let y_off = y+rowi as f32-1.0;
        let row = [
            src.get(x-1.0, y_off, c, true),
            src.get(x, y_off, c, true),
            src.get(x+1.0, y_off, c, true),
        ];

        let value = weight_quadratic(&row, x-x.floor());
        t[rowi as usize] = value;
    }

    weight_quadratic(&t, y-y.floor())
}


pub fn weight_cubic(span: &[u8], w: f32) -> u8 {
    // none of this is tested and was generated by chatgpt
    // let p0 = span[0] as f32;
    // let p1 = span[1] as f32;
    // let p2 = span[2] as f32;
    // let p3 = span[3] as f32;
    //
    // let value = p1 + 0.5 * w * (p2 - p0
    //     + w * (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3
    //     + w * (3.0 * (p1 - p2) + p3 - p0)));
    //
    // value.clamp(0.0, 255.0) as u8
    span[0]
}


pub fn blend_cubic(src: &PixelBuffer, x: f32, y: f32, c: u8) -> u8 {
    let mut t = [0u8; 4];
    for rowi in 0..4 {
        let y_off = rowi as f32-2.0;
        let row = [
            src.get(x-2.0, y_off, c, true),
            src.get(x-1.0, y_off, c, true),
            src.get(x+0.0, y_off, c, true),
            src.get(x+1.0, y_off, c, true),
        ];

        let value = weight_cubic(&row, x-x.floor());
        t[rowi as usize] = value;
    }

    weight_cubic(&t, y-y.floor())
}


pub fn _pt(src: PixelBuffer, quad: Quadrilateral, interpolation: isize) -> Result<PixelBuffer, String> {
    let projection = Projection::from_control_points(quad.as_array(), quad.dst_rect()).unwrap();
    let out_dim = quad.output_dimension();
    let c = src.channels;
    let mut dst = PixelBuffer::blank(out_dim.0 as u32, out_dim.1 as u32, c, src.interleaved);

    let h = get_transform(&projection);

    for c in 0..c {
        for dst_y in 0..dst.height as usize {
            let y = dst_y as f32;
            for dst_x in 0..dst.width as usize {
                let x = dst_x as f32;

                let denom = h[6] * x + h[7] * y + h[8];
                if denom == 0.0 {
                    continue;
                }

                let src_x = (h[0] * x + h[1] * y + h[2]) / denom;
                let src_y = (h[3] * x + h[4] * y + h[5]) / denom;

                if !src.in_bounds(src_x, src_y, c) {
                    continue;
                }
                let value: u8 = match interpolation {
                    0 => src.get(src_x, src_y, c, false),
                    1 => blend_linear(&src, src_x, src_y, c),
                    2 => blend_quadratic(&src, src_x, src_y, c),
                    3 => blend_cubic(&src, src_x, src_y, c),
                    _ => panic!("Invalid interpolation"),
                };
                *dst.at_mut(dst_x, dst_y, c) = value;
            }
        }
    }

    Ok(dst)
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

