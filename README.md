## WALNet Weak Label Analysis


This is an implementation for the paper "[A Closer Look at Weak Label Learning for Audio Events](https://arxiv.org/abs/1804.09288)". In this paper, we attempt to understand the challenges of large scale Audio Event Detection (AED) using weakly labeled data through a CNN based framework. Our network architecture is capable of handling variable length recordings and architecture design provides a way to control segment size of adjustable secondary outputs and thus these features eliminate the need for additional preprocessing steps. We look into how label density and label corruption affects performance and further compare mined web data as training data in comparison with manually labelled training data from AudioSet. We believe our work provides an approach to understand the challenges of weakly labeled learning and future AED works would benefit from our exploration. 

We provide the Audioset data (list of files used in our experimentation) provided for reproducibility.

If you have any question please contact - Ankit Shah - aps1@andrew.cmu.edu or Anurag Kumar - alnu@andrew.cmu.edu. 

### WALNet Architecture Diagram

![WALNet Architecture Diagram](https://github.com/ankitshah009/WALNet-Weak_Label_Analysis/blob/master/WALNet_Architecture_DIagram.jpg)

Reference
==========

<a href="https://arxiv.org/pdf/1804.09288.pdf"><img src="https://img.shields.io/badge/download%20paper-PDF-ff69b4.svg" alt="Download paper in PDF format" title="Download paper in PDF format" align="right" /></a>

If you use our repository for your research WALNet- weak label analysis, please cite our paper:

    
    @ARTICLE{2018arXiv180409288S,
    author = {{Shah}, A. and {Kumar}, A. and {Hauptmann}, A.~G. and {Raj}, B.
	  },
    title = "{A Closer Look at Weak Label Learning for Audio Events}",
    journal = {ArXiv e-prints},
    archivePrefix = "arXiv",
    eprint = {1804.09288},
    primaryClass = "cs.SD",
    keywords = {Computer Science - Sound, Computer Science - Learning, Computer Science - Multimedia, Electrical Engineering and Systems Science - Audio and Speech Processing},
    year = 2018,
    month = apr,
    adsurl = {http://adsabs.harvard.edu/abs/2018arXiv180409288S},
    adsnote = {Provided by the SAO/NASA Astrophysics Data System}
    }
    

