use argon2::{Algorithm, Argon2, Params, Version};
use nalgebra::{DMatrix, DVector};
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


pub struct HMatrix {
    h00: f32,
    h01: f32,
    h02: f32,
    h10: f32,
    h11: f32,
    h12: f32,
    h20: f32,
    h21: f32,
    h22: f32,
}

impl HMatrix {
    pub fn map(&self, c: &Point) -> Point {
        let denom = self.h20*c.x + self.h21*c.y + self.h22;
        Point{
            x: (self.h00*c.x + self.h01*c.y + self.h02)/denom,
            y: (self.h10*c.x + self.h11*c.y + self.h12)/denom,
        }
    }

}


pub fn midpoint(a: &Point, b: &Point) -> Point {
    Point{x: (a.x+b.x)/2.0, y: (a.y+b.y)/2.0}
}


pub fn distance(a: &Point, b: &Point) -> f32 {
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
            dst[col*height+row] = src[row*width+col];
        }
    }

    Ok(())
}


#[derive(Serialize, Deserialize)]
pub struct PixelBuffer {
    pub width: usize,
    pub height: usize,
    pub channels: usize,
    pub interleaved: bool,
    pub data: Vec<u8>,
}


impl PixelBuffer {

    pub fn new(width: usize, height: usize, channels: usize, interleaved: bool, src: &[u8]) -> Result<Self, String> {
        if width*height*channels != src.len() {
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

    pub fn blank(width: usize, height: usize, channels: usize, interleaved: bool) -> Self {
        Self {
            width,
            height,
            channels,
            interleaved,
            data: vec![0u8; width*height*channels],
        }
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

    pub fn in_bounds(&self, x: f32, y: f32, c: usize) -> bool {
        let (w, h) = (self.width as f32, self.height as f32);
        0.0 <= x && x < w && 0.0 <= y && y < h && c < self.channels
    }

    pub unsafe fn unsafe_index(&self, x: usize, y: usize, c: usize) -> usize {
        let (w, h) = (self.width, self.height);
        if self.interleaved {
            let pixel_size = self.channels;
            y*pixel_size*w + x*pixel_size + c
        } else {
            let channel_size = w*h;
            c*channel_size + y*w + x
        }
    }

    pub fn at(&self, mut x: f32, mut y: f32, c: usize, closest: bool) -> u8 {
        if !self.in_bounds(x, y, c) {
            if closest {
                x = x.clamp(0.0, self.width as f32-1.0);
                y = y.clamp(0.0, self.height as f32-1.0);
            } else {
                return 0u8;
            }
        }
        let i = unsafe { self.unsafe_index(x as usize, y as usize, c) };
        self.data[i]
    }

    pub fn at_mut(&mut self, x: usize, y: usize, c: usize) -> &mut u8 {
        if !self.in_bounds(x as f32, y as f32, c) {
            panic!("Index out of bounds: x={}, y={}, c={}", x, y, c);
        }
        let i = unsafe { self.unsafe_index(x, y, c) };
        &mut self.data[i]
    }
}


pub struct FloatBuffer {
    pub width: usize,
    pub height: usize,
    pub channels: usize,
    pub margin: usize,
    pub data: Vec<f32>,
}


impl FloatBuffer {

    pub fn from_pixel_buffer(src: PixelBuffer, margin: usize) -> Self {
        let mut dst = Self {
            width: margin+src.width+margin,
            height: margin+src.height+margin,
            channels: src.channels,
            margin,
            data: vec![0f32; src.channels*(margin+src.width+margin)*(margin+src.height+margin)],
        };


        if src.interleaved {
            for channel in 0..src.channels {
                for row in 0..src.height {
                    let off = (channel*dst.height*dst.width)+(row+margin)*dst.width+margin;
                    let dst_slice: &mut [f32] = &mut dst.data[off..off+src.width];
                    assert_eq!(src.width, dst_slice.len());
                    for col in 0..src.width {
                        let v = src.data[row*src.width*src.channels+col*src.channels+channel] as f32;
                        dst_slice[col] = v;
                    }
                }
            }
        } else {
            for channel in 0..src.channels {
                for row in 0..src.height {
                    let off = (channel*dst.height*dst.width)+(row+margin)*dst.width+margin;
                    let dst_slice: &mut [f32] = &mut dst.data[off..off+src.width];
                    let off = (channel*src.height*src.width)+row*src.width;
                    let src_slice: &[u8] = &src.data[off..off+src.width];
                    assert_eq!(src.width, dst_slice.len());
                    assert_eq!(src.width, src_slice.len());
                    for col in 0..src.width {
                        let v = src_slice[col] as f32;
                        dst_slice[col] = v;
                    }
                }
            }
        }

        dst
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
    pub fn output_dimension(&self) -> (f32, f32) {
        let left_mid = midpoint(&self.tl, &self.bl);
        let right_mid = midpoint(&self.tr, &self.br);
        let width = distance(&left_mid, &right_mid);

        let top_mid = midpoint(&self.tl, &self.tr);
        let bot_mid = midpoint(&self.bl, &self.br);
        let height = distance(&top_mid, &bot_mid);

        (width.floor(), height.floor())
    }

    pub fn dst_quad(&self) -> Self {
        let (width, height) = self.output_dimension();

        Self {
            tl: Point{x: 0.0,   y: 0.0},
            tr: Point{x: width, y: 0.0},
            br: Point{x: width, y: height},
            bl: Point{x: 0.0,   y: height}
        }
    }
}


pub fn calculate_homography_matrix(s: &Quadrilateral, d: &Quadrilateral) -> HMatrix {
    let a = DMatrix::from_row_slice(8, 8, &[
        0.0,    0.0,    0.0, -s.tl.x, -s.tl.y, -1.0,  d.tl.y*s.tl.x,  d.tl.y*s.tl.y,
        s.tl.x, s.tl.y, 1.0,  0.0,     0.0,     0.0, -d.tl.x*s.tl.x, -d.tl.x*s.tl.y,
        0.0,    0.0,    0.0, -s.tr.x, -s.tr.y, -1.0,  d.tr.y*s.tr.x,  d.tr.y*s.tr.y,
        s.tr.x, s.tr.y, 1.0,  0.0,     0.0,     0.0, -d.tr.x*s.tr.x, -d.tr.x*s.tr.y,
        0.0,    0.0,    0.0, -s.br.x, -s.br.y, -1.0,  d.br.y*s.br.x,  d.br.y*s.br.y,
        s.br.x, s.br.y, 1.0,  0.0,     0.0,     0.0, -d.br.x*s.br.x, -d.br.x*s.br.y,
        0.0,    0.0,    0.0, -s.bl.x, -s.bl.y, -1.0,  d.bl.y*s.bl.x,  d.bl.y*s.bl.y,
        s.bl.x, s.bl.y, 1.0,  0.0,     0.0,     0.0, -d.bl.x*s.bl.x, -d.bl.x*s.bl.y,
    ]);

    let b = DVector::from_column_slice(&[
        -d.tl.y,
         d.tl.x,
        -d.tr.y,
         d.tr.x,
        -d.br.y,
         d.br.x,
        -d.bl.y,
         d.bl.x
    ]);

    let solution = a.lu().solve(&b).unwrap();
    let t = solution.as_slice();
    HMatrix{
        h00: t[0],
        h01: t[1],
        h02: t[2],
        h10: t[3],
        h11: t[4],
        h12: t[5],
        h20: t[6],
        h21: t[7],
        h22: 1f32,
    }
}


pub fn weight_cubic(p0: f32, p1: f32, p2: f32, p3: f32, w: f32) -> f32 {
    let value = p1 + 0.5 * w * (p2 - p0
        + w * (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3
        + w * (3.0 * (p1 - p2) + p3 - p0)));

    value.clamp(0.0, 255.0)
}


pub fn blend_cubic(src: &PixelBuffer, x: f32, y: f32, c: usize) -> u8 {
    let mut t = [0f32; 4];
    for rowi in 0..4usize {
        let y_off = y+rowi as f32-2.0;
        let p0 = src.at(x-2.0, y_off, c, true) as f32;
        let p1 = src.at(x-1.0, y_off, c, true) as f32;
        let p2 = src.at(x+0.0, y_off, c, true) as f32;
        let p3 = src.at(x+1.0, y_off, c, true) as f32;

        let value = weight_cubic(p0, p1, p2, p3, x-x.floor());
        t[rowi] = value;
    }

    weight_cubic(t[0], t[1], t[2], t[3], y-y.floor()) as u8
}


pub fn _pt(mut src: PixelBuffer, quad: Quadrilateral) -> Result<PixelBuffer, String> {
    let out_dim = quad.output_dimension();
    let c = src.channels;
    let mut dst = PixelBuffer::blank(out_dim.0 as usize, out_dim.1 as usize, c, false);
    let interleaved = src.interleaved;
    // convert to planar
    // if src.interleaved {
    //     src.toggle_interleaved();
    // }
    let h = calculate_homography_matrix(&quad.dst_quad(), &quad);

    let fb = FloatBuffer::from_pixel_buffer(src, 2);

    for channel in 0..dst.channels {
        for row in 0..dst.height {
            let dst_off = channel*dst.height*dst.width + row*dst.width;
            let dst_slice = &mut dst.data[dst_off..dst_off+dst.width];
            for col in 0..dst.width {
                let dp = Point{x: col as f32, y: row as f32};
                let sp = h.map(&dp);
                // assert!(src.in_bounds(sp.x, sp.y, channel));
                let weight = sp.x-sp.x.floor();

                let src_off = channel*fb.height*fb.width + (sp.y+0.0) as usize*fb.width + sp.x as usize;
                let ss = &fb.data[src_off..src_off+4];
                let r0 = weight_cubic(ss[0], ss[1], ss[2], ss[3], weight);

                let src_off = channel*fb.height*fb.width + (sp.y+1.0) as usize*fb.width + sp.x as usize;
                let ss = &fb.data[src_off..src_off+4];
                let r1 = weight_cubic(ss[0], ss[1], ss[2], ss[3], weight);

                let src_off = channel*fb.height*fb.width + (sp.y+2.0) as usize*fb.width + sp.x as usize;
                let ss = &fb.data[src_off..src_off+4];
                let r2 = weight_cubic(ss[0], ss[1], ss[2], ss[3], weight);

                let src_off = channel*fb.height*fb.width + (sp.y+3.0) as usize*fb.width + sp.x as usize;
                let ss = &fb.data[src_off..src_off+4];
                let r3 = weight_cubic(ss[0], ss[1], ss[2], ss[3], weight);

                let w = weight_cubic(r0, r1, r2, r3, sp.y-sp.y.floor());
                dst_slice[col] = w as u8;
            }
        }
    }

    if interleaved != dst.interleaved {
        dst.toggle_interleaved();
    }
    Ok(dst)
}

