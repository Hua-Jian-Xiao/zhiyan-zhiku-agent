from django.core.management.base import BaseCommand

from seed.builder import run_seed


class Command(BaseCommand):
    help = "Seed the 智研知库 demo knowledge base, graph, users and RAG settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing business data before seeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding 智研知库...")
        stats = run_seed(reset=options["reset"])
        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete: "
                + ", ".join(f"{key}={value}" for key, value in stats.items())
            )
        )
        self.stdout.write("Demo accounts: student / student123, admin / zhiyan123")
