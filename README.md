# Submission 2: Alzheimer's Disease Detection
Nama: Bima Prastyaji

Username dicoding: Bima Prastyaji

| | Deskripsi |
| ----------- | ----------- |
| Dataset | [Alzheimer's Disease Dataset](https://www.kaggle.com/datasets/rabieelkharoua/alzheimers-disease-dataset) |
| Masalah | Penyakit Alzheimer's adalah gangguan neurodegeneratif progresif yang terutama mempengaruhi fungsi kognitif dan memori. Masalah utama yang terkait dengan penyakit ini adalah penurunan kemampuan berpikir, mengingat, dan membuat keputusan, yang secara bertahap memperburuk kualitas hidup penderitanya. Faktor yang dapat menyebabkan penyakit alzheimer's antara lain genetik, lingkungan, dan gaya hidup. Selain itu, penyakit ini seringkali sulit didiagnosis pada tahap awal, sehingga pencegahannya dan pengobatannya sulit. |
| Solusi machine learning | Dengan memanfaatkan teknologi saat ini, machine learning menjadi salah satu solusi dalam mendeteksi suatu penyakit pada dunia medis.  Adanya sebuah sistem deteksi penyakit alzheimer's ini diharapkan para tenaga medis dapat mendeteksi penyakit lebih awal untuk mencegah penyebaran. |
| Metode pengolahan | - |
| Arsitektur model | - |
| Metrik evaluasi | Metrik evaluasi yang digunakan yaitu AUC, Precision, Recall, ExampleCount dan BinaryAccuracy |
| Performa model | Performa model sudah cukup bagus yaitu dengan nilai binary_accuracy mencapai 98% dengan loss 0.0383 pada training, namun pada evaluasi nilai val_binary_accuracy hanya mencapai 80% dengan loss 2.2723. Hal ini menunjukkan bahwa model mengalami overfitting, namun demikian model sudah dapat memberikan prediksi dengan baik|
| Opsi deployment | Proyek machine learning ini dideploy menggunakan salah satu platfrom as a service yaitu [Railway](https://railway.app/) yang menyediakan layanan gratis untuk mendeploy sebuah proyek. |
| Web app | [alzheimers-model](https://mlops-prediction-production.up.railway.app/v1/models/alzheimer_model/metadata)|
| Monitoring | - |