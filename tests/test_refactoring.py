"""Pengujian otomatis untuk memvalidasi seluruh fungsionalitas hasil refactoring."""

import os
import shutil
import tempfile
import unittest

from autosign.models import Profile, SignatureConfig, AppSettings, ProcessingTask
from autosign.services.signature_resolver import SignatureResolver
from autosign.services.profile_service import ProfileService
from autosign.services.settings_service import SettingsService
from autosign.services.batch_scanner import BatchScanner
from autosign.services.metrics_tracker import MetricsTracker


class TestAutoSignRefactoring(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_models_serialization(self):
        sig = SignatureConfig(label="TTD_Direktur", rel_x=0.1, rel_y=0.2, rel_w=0.15, rel_h=0.08)
        d = sig.to_dict()
        self.assertEqual(d["label"], "TTD_Direktur")

        reconstructed_sig = SignatureConfig.from_dict(d)
        self.assertEqual(reconstructed_sig.label, sig.label)
        self.assertAlmostEqual(reconstructed_sig.rel_x, 0.1)

        prof = Profile(name="TestProf", keywords=["KARTIR", "SURAT"], signatures=[sig])
        prof_dict = prof.to_dict()
        reconstructed_prof = Profile.from_dict(prof_dict)
        self.assertEqual(reconstructed_prof.name, "TestProf")
        self.assertEqual(len(reconstructed_prof.signatures), 1)

    def test_profile_service_crud_and_no_duplication(self):
        prof_dir = os.path.join(self.test_dir, "profiles")
        service = ProfileService(profiles_dir=prof_dir)

        sig = SignatureConfig(label="TTD_1", rel_x=0.5, rel_y=0.5, rel_w=0.1, rel_h=0.1)
        prof = Profile(name="Invoice_Profile", keywords=["INV", "TAGIHAN"], signatures=[sig])

        # 1. Save
        saved_file = service.save_profile(prof)
        self.assertEqual(saved_file, "Invoice_Profile.json")
        self.assertTrue(os.path.exists(os.path.join(prof_dir, "Invoice_Profile.json")))

        # 2. List
        profiles = service.list_profiles()
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0][1].name, "Invoice_Profile")

        # 3. Duplicate
        dup_prof = service.duplicate_profile(prof)
        self.assertEqual(dup_prof.name, "Invoice_Profile_Copy")
        profiles_after_dup = service.list_profiles()
        self.assertEqual(len(profiles_after_dup), 2)

        # 4. Delete
        del_result = service.delete_profile(saved_file)
        self.assertTrue(del_result)
        self.assertEqual(len(service.list_profiles()), 1)

    def test_signature_resolver_hierarchy(self):
        ttd_root = os.path.join(self.test_dir, "ttd_master")
        os.makedirs(ttd_root, exist_ok=True)

        # Level 3: Root fallback
        root_img = os.path.join(ttd_root, "paraf.png")
        with open(root_img, "w") as f:
            f.write("dummy")

        res_root = SignatureResolver.resolve(ttd_root, "divisi_a/proyek_b/doc.pdf", "paraf")
        self.assertEqual(res_root, root_img)

        # Level 2: Parent folder segment
        seg_dir = os.path.join(ttd_root, "divisi_a")
        os.makedirs(seg_dir, exist_ok=True)
        seg_img = os.path.join(seg_dir, "paraf.png")
        with open(seg_img, "w") as f:
            f.write("dummy")

        res_seg = SignatureResolver.resolve(ttd_root, "divisi_a/proyek_b/doc.pdf", "paraf")
        self.assertEqual(res_seg, seg_img)

        # Level 1: Exact relative directory
        exact_dir = os.path.join(ttd_root, "divisi_a", "proyek_b")
        os.makedirs(exact_dir, exist_ok=True)
        exact_img = os.path.join(exact_dir, "paraf.png")
        with open(exact_img, "w") as f:
            f.write("dummy")

        res_exact = SignatureResolver.resolve(ttd_root, "divisi_a/proyek_b/doc.pdf", "paraf")
        self.assertEqual(res_exact, exact_img)

    def test_batch_scanner(self):
        pdf_root = os.path.join(self.test_dir, "pdf_in")
        output_dir = os.path.join(self.test_dir, "pdf_out")
        ttd_root = os.path.join(self.test_dir, "ttd")
        sub_dir = os.path.join(pdf_root, "2026")
        os.makedirs(sub_dir, exist_ok=True)

        # Create dummy PDF files
        pdf1 = os.path.join(sub_dir, "KARTIR_001.pdf")
        pdf2 = os.path.join(sub_dir, "LAINNYA_002.pdf")
        with open(pdf1, "w") as f: f.write("dummy")
        with open(pdf2, "w") as f: f.write("dummy")

        prof = Profile(name="Kartir_Prof", keywords=["KARTIR"], signatures=[])

        tasks = BatchScanner.scan_files(
            pdf_root=pdf_root,
            ttd_root=ttd_root,
            output_dir=output_dir,
            profiles=[prof],
            skip_processed=True
        )

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].pdf_path, pdf1)

    def test_metrics_tracker(self):
        tracker = MetricsTracker()
        tracker.start_time -= 2.0  # simulate 2 seconds elapsed
        speed, eta = tracker.calculate_progress(completed=10, total=20)
        self.assertGreater(speed, 0.0)
        self.assertNotEqual(eta, "...")

    def test_pdf_sign_engine_end_to_end(self):
        import fitz
        from PIL import Image
        import threading
        from autosign.services.pdf_engine import PdfSignEngine

        # 1. Create a real sample PDF using PyMuPDF
        pdf_dir = os.path.join(self.test_dir, "input_pdf")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, "sample.pdf")

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 100), "Dokumen Uji Coba AutoSign")
        doc.save(pdf_path)
        doc.close()

        # 2. Create a real signature image PNG
        ttd_dir = os.path.join(self.test_dir, "ttd_master")
        os.makedirs(ttd_dir, exist_ok=True)
        sig_img_path = os.path.join(ttd_dir, "TTD_Test.png")
        img = Image.new("RGBA", (100, 50), color=(0, 122, 194, 255))
        img.save(sig_img_path)

        # 3. Setup task
        out_pdf_path = os.path.join(self.test_dir, "output_pdf", "sample.pdf")
        sig_cfg = SignatureConfig(label="TTD_Test", rel_x=0.5, rel_y=0.7, rel_w=0.2, rel_h=0.1)
        prof = Profile(name="TestProfile", keywords=["sample"], signatures=[sig_cfg])

        task = ProcessingTask(
            pdf_path=pdf_path,
            save_path=out_pdf_path,
            profile=prof,
            ttd_root=ttd_dir,
            rel_path="sample.pdf"
        )

        cache = {}
        lock = threading.Lock()
        result = PdfSignEngine.process_task(task, cache, lock)

        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(out_pdf_path))
        self.assertIn(sig_img_path, cache)  # Cache populated!

        # Verify output PDF has the image inserted
        with fitz.open(out_pdf_path) as out_doc:
            self.assertEqual(len(out_doc), 1)
            img_list = out_doc[0].get_images()
            self.assertEqual(len(img_list), 1)

    def test_pdf_sign_engine_multi_page(self):
        import fitz
        from PIL import Image
        import threading
        from autosign.services.pdf_engine import PdfSignEngine

        # 1. Create a 3-page PDF
        pdf_dir = os.path.join(self.test_dir, "input_multi")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, "multi_sample.pdf")

        doc = fitz.open()
        for i in range(3):
            p = doc.new_page(width=595, height=842)
            p.insert_text((50, 50), f"Halaman ke-{i+1}")
        doc.save(pdf_path)
        doc.close()

        # 2. Create signature images
        ttd_dir = os.path.join(self.test_dir, "ttd_multi")
        os.makedirs(ttd_dir, exist_ok=True)
        sig1 = os.path.join(ttd_dir, "Paraf_Awal.png")
        sig2 = os.path.join(ttd_dir, "TTD_Akhir.png")
        Image.new("RGBA", (80, 40), (255, 0, 0, 255)).save(sig1)
        Image.new("RGBA", (80, 40), (0, 255, 0, 255)).save(sig2)

        # 3. Setup signatures on Page 0 and Page -1 (last page = page 2)
        out_pdf_path = os.path.join(self.test_dir, "output_multi", "multi_sample.pdf")
        sig_cfg1 = SignatureConfig(label="Paraf_Awal", rel_x=0.1, rel_y=0.1, rel_w=0.1, rel_h=0.05, page=0)
        sig_cfg2 = SignatureConfig(label="TTD_Akhir", rel_x=0.7, rel_y=0.8, rel_w=0.15, rel_h=0.08, page=-1)
        prof = Profile(name="MultiProfile", keywords=["multi"], signatures=[sig_cfg1, sig_cfg2])

        task = ProcessingTask(
            pdf_path=pdf_path,
            save_path=out_pdf_path,
            profile=prof,
            ttd_root=ttd_dir,
            rel_path="multi_sample.pdf"
        )

        result = PdfSignEngine.process_task(task, {}, threading.Lock())
        self.assertTrue(result.success)

        # 4. Verify pages
        with fitz.open(out_pdf_path) as out_doc:
            self.assertEqual(len(out_doc), 3)
            # Halaman 0 harus ada stempel
            self.assertEqual(len(out_doc[0].get_images()), 1)
            # Halaman 1 tidak ada stempel
            self.assertEqual(len(out_doc[1].get_images()), 0)
            # Halaman 2 (halaman terakhir) harus ada stempel
            self.assertEqual(len(out_doc[2].get_images()), 1)

    def test_logger_setup(self):
        from autosign.services.logger import setup_logger, get_logger
        log_file = os.path.join(self.test_dir, "test.log")
        logger = setup_logger(log_file=log_file)
        logger.info("Test log entry")
        self.assertTrue(os.path.exists(log_file))


if __name__ == "__main__":
    unittest.main()

