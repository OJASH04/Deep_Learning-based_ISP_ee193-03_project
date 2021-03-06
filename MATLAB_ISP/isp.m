function img = isp(raw, metadata);

iso = metadata_value(metadata, 'ISO')

img = blacklevel(raw);
img = isp_demosaic(img);
img = colorcorrection(img);
img = denoise(img);
img = cameracurve(img);