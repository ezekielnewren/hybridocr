use std::fmt::{Debug, Formatter};
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
    pub fn map(&self, x: f32, y: f32) -> Point {
        let denom = self.h20*x + self.h21*y + self.h22;
        Point{
            x: (self.h00*x + self.h01*y + self.h02)/denom,
            y: (self.h10*x + self.h11*y + self.h12)/denom,
        }
    }

}


pub fn midpoint(a: &Point, b: &Point) -> Point {
    Point{x: (a.x+b.x)/2.0, y: (a.y+b.y)/2.0}
}


pub fn distance(a: &Point, b: &Point) -> f32 {
    ((a.x-b.x).powi(2) + (a.y-b.y).powi(2)).sqrt()
}

#[derive(Serialize, Deserialize)]
pub struct PixelBuffer {
    pub width: usize,
    pub height: usize,
    pub channels: usize,
    pub data: Vec<u8>,
}


impl PixelBuffer {

    pub fn blank(width: usize, height: usize, channels: usize) -> Self {
        Self {
            width,
            height,
            channels,
            data: vec![0; width*height*channels],
        }
    }

    pub fn in_bounds(&self, quad: &Quadrilateral, margin: usize) -> bool {
        let (x_min, x_max) = (margin as f32, (self.width-1-margin) as f32);
        let (y_min, y_max) = (margin as f32, (self.height-1-margin) as f32);
        for p in [&quad.tl, &quad.tr, &quad.br, &quad.bl] {
            if !(x_min <= p.x && p.x <= x_max) {
                return false;
            }
            if !(y_min <= p.y && p.y <= y_max) {
                return false;
            }
        }

        true
    }
}


impl Debug for Quadrilateral {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.write_fmt(format_args!("tl: {:?}, {:?}, ", self.tl.x, self.tl.y))?;
        f.write_fmt(format_args!("tr: {:?}, {:?}, ", self.tr.x, self.tr.y))?;
        f.write_fmt(format_args!("br: {:?}, {:?}, ", self.br.x, self.br.y))?;
        f.write_fmt(format_args!("bl: {:?}, {:?}", self.bl.x, self.bl.y))
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

    pub fn from_data(p: &[f32]) -> Self {
        Self {
            tl: Point{ x: p[0], y: p[1] },
            tr: Point{ x: p[2], y: p[3] },
            br: Point{ x: p[4], y: p[5] },
            bl: Point{ x: p[6], y: p[7] },
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


pub fn _pt(src: PixelBuffer, quad: Quadrilateral) -> Result<PixelBuffer, String> {
    assert!(src.in_bounds(&quad, 0));

    let margin = 2usize;
    let dim = quad.output_dimension();
    let cw = src.channels;
    let mut dst = PixelBuffer::blank(dim.0 as usize, dim.1 as usize, cw);
    let hmat = calculate_homography_matrix(&quad.dst_quad(), &quad);
    let mut run = [0f32; 4];

    let mut row = 0usize;
    let mut col = 0usize;
    let mut channel = 0usize;
    for sink in dst.data.as_mut_slice() {
        let sp = hmat.map(col as f32, row as f32);
        let x = sp.x.clamp(margin as f32, (src.width-1-margin) as f32) as usize;
        let y = sp.y.clamp(margin as f32, (src.height-1-margin) as f32) as usize;
        let x_weight = sp.x-sp.x.floor();
        let y_weight = sp.y-sp.y.floor();

        for i in 0..4 {
            let src_off = (y-margin+i)*src.width*cw + (x-margin)*cw;
            let p = &src.data[src_off..src_off+4*cw];
            let c0 = p[0*cw+channel] as f32;
            let c1 = p[1*cw+channel] as f32;
            let c2 = p[2*cw+channel] as f32;
            let c3 = p[3*cw+channel] as f32;
            run[i] = weight_cubic(c0, c1, c2, c3, x_weight);
        }
        let w = weight_cubic(run[0], run[1], run[2], run[3], y_weight) as u8;
        *sink = w;

        channel += 1;
        if channel == cw {
            channel = 0;
            col += 1;
        }
        if col == dst.width {
            col = 0;
            row += 1;
        }
    }

    Ok(dst)
}

