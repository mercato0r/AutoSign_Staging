"""Layanan pemindaian direktori dan pencocokan profil dokumen PDF."""

import os
from typing import List, Optional
from autosign.models import Profile, ProcessingTask


class BatchScanner:
    """Memindai file PDF pada direktori root dan mencocokkannya dengan profil aktif."""

    @staticmethod
    def scan_files(
        pdf_root: str,
        ttd_root: str,
        output_dir: str,
        profiles: List[Profile],
        skip_processed: bool = True
    ) -> List[ProcessingTask]:
        tasks: List[ProcessingTask] = []

        if not os.path.exists(pdf_root) or not profiles:
            return tasks

        for root_dir, _, files in os.walk(pdf_root):
            for file_name in files:
                if file_name.lower().endswith(".pdf"):
                    full_path = os.path.join(root_dir, file_name)
                    rel_path = os.path.relpath(full_path, pdf_root)
                    save_path = os.path.join(output_dir, rel_path)

                    # Lewati jika sudah diproses sebelumnya dan opsi skip_processed aktif
                    if skip_processed and os.path.exists(save_path):
                        continue

                    # Cocokkan dengan salah satu kata kunci profil
                    matched_profile: Optional[Profile] = None
                    full_path_lower = full_path.lower()

                    for prof in profiles:
                        if any(kw.lower() in full_path_lower for kw in prof.keywords):
                            matched_profile = prof
                            break

                    if matched_profile:
                        tasks.append(
                            ProcessingTask(
                                pdf_path=full_path,
                                save_path=save_path,
                                profile=matched_profile,
                                ttd_root=ttd_root,
                                rel_path=rel_path
                            )
                        )

        return tasks
