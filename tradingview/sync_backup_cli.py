#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TradingView Data Sync and Backup CLI Tool
Provides a command-line interface for managing data synchronization, backup, and restore operations.
"""

import asyncio
import argparse
import json
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from data_sync_backup import (
    DataSyncBackupController,
    SyncTask,
    BackupType,
    SyncStatus
)
from tradingview.utils import get_logger

logger = get_logger(__name__)


class SyncBackupCLI:
    """CLI for data synchronization and backup"""

    def __init__(self, config_file: str = None):
        """Initialize the CLI"""
        self.config_file = config_file or "tradingview/sync_backup_config.yaml"
        self.config = self._load_config()
        self.controller = DataSyncBackupController(self.config)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file"""
        config_path = Path(self.config_file)

        if not config_path.exists():
            logger.warning(f"Configuration file does not exist: {self.config_file}, using default config")
            return self._get_default_config()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration file: {self.config_file}")
                return config
        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'sync_config': {
                'sync_interval': 300,
                'batch_size': 100,
                'max_concurrent_tasks': 5
            },
            'backup_config': {
                'backup_dir': 'data/backups',
                'max_backup_files': 30,
                'compression_enabled': True
            },
            'schedule_enabled': False  # Scheduled tasks disabled by default in CLI mode
        }

    async def run_command(self, args):
        """Execute CLI command"""
        try:
            if args.command == 'status':
                await self._cmd_status(args)
            elif args.command == 'backup':
                await self._cmd_backup(args)
            elif args.command == 'restore':
                await self._cmd_restore(args)
            elif args.command == 'sync':
                await self._cmd_sync(args)
            elif args.command == 'list':
                await self._cmd_list(args)
            elif args.command == 'daemon':
                await self._cmd_daemon(args)
            elif args.command == 'test':
                await self._cmd_test(args)
            else:
                print(f"Unknown command: {args.command}")
                sys.exit(1)

        except KeyboardInterrupt:
            print("\nOperation interrupted by user")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)

    async def _cmd_status(self, args):
        """View system status"""
        print("🔍 Retrieving system status...")

        # Start controller to get status
        await self.controller.start()

        try:
            status = self.controller.get_system_status()

            print("\n" + "="*60)
            print(" TradingView Data Sync & Backup System Status")
            print("="*60)

            # Sync engine status
            sync_status = status.get('sync_engine', {})
            print(f"\n📡 Sync Engine:")
            print(f"  Status: {'🟢 Running' if sync_status.get('is_running') else '🔴 Stopped'}")
            print(f"  Active Tasks: {sync_status.get('active_tasks', 0)}")
            print(f"  Completed Tasks: {sync_status.get('completed_tasks', 0)}")
            print(f"  Failed Tasks: {sync_status.get('failed_tasks', 0)}")
            print(f"  Queue Size: {sync_status.get('queue_size', 0)}")

            stats = sync_status.get('statistics', {})
            print(f"  Total Records Synced: {stats.get('total_synced', 0)}")
            print(f"  Total Failures: {stats.get('total_failed', 0)}")
            print(f"  Sync Speed: {stats.get('sync_speed', 0):.2f} records/sec")

            # Backup manager status
            backup_status = status.get('backup_manager', {})
            print(f"\n💾 Backup Manager:")
            print(f"  Total Backups: {backup_status.get('total_backups', 0)}")
            print(f"  Total Size: {backup_status.get('total_size_mb', 0):.2f} MB")
            print(f"  Backup Directory: {backup_status.get('backup_dir', 'N/A')}")

            # Recent backup records
            records = backup_status.get('backup_records', [])
            if records:
                print(f"\n📋 Recent Backup Records (last 5):")
                for record in records[-5:]:
                    created_time = datetime.fromtimestamp(record['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  • {record['backup_id'][:20]}... ({record['backup_type']}) - {created_time} - {record['size_bytes']/1024/1024:.1f}MB")

            print(f"\n⏰ System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🔧 Scheduled Tasks: {'Enabled' if status.get('schedule_enabled') else 'Disabled'}")

        finally:
            await self.controller.stop()

    async def _cmd_backup(self, args):
        """Create a new backup"""
        backup_type_map = {
            'full': BackupType.FULL,
            'incremental': BackupType.INCREMENTAL,
            'snapshot': BackupType.SNAPSHOT
        }

        if args.type not in backup_type_map:
            print(f"Error: Unsupported backup type '{args.type}'")
            print("Supported types: full, incremental, snapshot")
            sys.exit(1)

        backup_type = backup_type_map[args.type]
        symbols = args.symbols.split(',') if args.symbols else None
        timeframes = args.timeframes.split(',') if args.timeframes else None

        print(f"🎯 Starting {args.type} backup creation...")
        if symbols:
            print(f"   Symbols: {', '.join(symbols)}")
        if timeframes:
            print(f"   Timeframes: {', '.join(timeframes)}")

        await self.controller.start()

        try:
            backup_id = await self.controller.create_manual_backup(
                backup_type, symbols, timeframes
            )

            if backup_id:
                print(f"✅ Backup created successfully!")
                print(f"   Backup ID: {backup_id}")

                # Get backup details
                backup_info = self.controller.backup_manager.get_backup_info(backup_id)
                if backup_info:
                    print(f"   File Size: {backup_info['size_bytes']/1024/1024:.2f} MB")
                    created_time = datetime.fromtimestamp(backup_info['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"   Created At: {created_time}")
                    print(f"   Data Range: {backup_info['symbols_count']} symbols")
            else:
                print("❌ Failed to create backup")
                sys.exit(1)

        finally:
            await self.controller.stop()

    async def _cmd_restore(self, args):
        """Restore from a backup"""
        print(f"🔄 Starting restore from backup: {args.backup_id}")

        await self.controller.start()

        try:
            # Check if backup exists
            backup_info = self.controller.backup_manager.get_backup_info(args.backup_id)
            if not backup_info:
                print(f"❌ Backup not found: {args.backup_id}")
                sys.exit(1)

            print(f"   Backup Type: {backup_info['backup_type']}")
            print(f"   Backup Size: {backup_info['size_bytes']/1024/1024:.2f} MB")
            created_time = datetime.fromtimestamp(backup_info['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"   Created At: {created_time}")

            if not args.force:
                confirm = input("Confirm restore from this backup? (y/N): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled")
                    return

            success = await self.controller.restore_from_backup(
                args.backup_id, args.target_db
            )

            if success:
                print("✅ Backup restore successful!")
                if args.target_db:
                    print(f"   Restored to: {args.target_db}")
                else:
                    print("   Restored to: Cache system")
            else:
                print("❌ Failed to restore backup")
                sys.exit(1)

        finally:
            await self.controller.stop()

    async def _cmd_sync(self, args):
        """Execute data synchronization"""
        if args.source not in ['primary', 'cache', 'backup']:
            print("Error: source must be primary, cache, or backup")
            sys.exit(1)

        if args.target not in ['cache', 'backup', 'remote']:
            print("Error: target must be cache, backup, or remote")
            sys.exit(1)

        symbols = args.symbols.split(',') if args.symbols else ['BINANCE:BTCUSDT']
        timeframes = args.timeframes.split(',') if args.timeframes else ['15']

        print(f"🔄 Starting data synchronization:")
        print(f"   Source: {args.source}")
        print(f"   Target: {args.target}")
        print(f"   Symbols: {', '.join(symbols)}")
        print(f"   Timeframes: {', '.join(timeframes)}")

        await self.controller.start()

        try:
            task_id = await self.controller.sync_data(
                args.source, args.target, symbols, timeframes
            )

            print(f"✅ Sync task added: {task_id}")

            # Wait for task completion
            if args.wait:
                print("⏳ Waiting for task completion...")

                for i in range(30):  # Wait up to 30 seconds
                    await asyncio.sleep(1)
                    status = self.controller.get_system_status()

                    # Check if task is completed
                    sync_status = status.get('sync_engine', {})
                    if sync_status.get('active_tasks', 0) == 0:
                        print("✅ Sync task completed!")
                        break

                    print(f"   Progress: {i+1}/30s")
                else:
                    print("⚠️  Task still in progress, please check status later")

        finally:
            await self.controller.stop()

    async def _cmd_list(self, args):
        """List backups or tasks"""
        if args.type == 'backups':
            await self._list_backups(args)
        elif args.type == 'tasks':
            await self._list_tasks(args)
        else:
            print("Error: type must be backups or tasks")
            sys.exit(1)

    async def _list_backups(self, args):
        """List all available backups"""
        print("📋 Backup List:")

        await self.controller.start()

        try:
            backup_info = self.controller.backup_manager.get_backup_info()
            records = backup_info.get('backup_records', [])

            if not records:
                print("   No backup records found")
                return

            # Sort by creation time descending
            records.sort(key=lambda x: x['created_at'], reverse=True)

            print(f"\nTotal: {len(records)} backups, total size {backup_info.get('total_size_mb', 0):.2f} MB\n")

            # Table header
            print(f"{'Backup ID':<25} {'Type':<12} {'Size(MB)':<10} {'Symbols':<8} {'Created At':<20}")
            print("-" * 80)

            # Display backup records
            for record in records:
                backup_id = record['backup_id'][:22] + "..." if len(record['backup_id']) > 25 else record['backup_id']
                size_mb = record['size_bytes'] / 1024 / 1024
                created_time = datetime.fromtimestamp(record['created_at']).strftime('%Y-%m-%d %H:%M:%S')

                print(f"{backup_id:<25} {record['backup_type']:<12} {size_mb:<10.2f} {record['symbols_count']:<8} {created_time:<20}")

            if args.verbose:
                print(f"\nBackup Directory: {backup_info.get('backup_dir')}")

        finally:
            await self.controller.stop()

    async def _list_tasks(self, args):
        """List current sync tasks"""
        print("📋 Sync Task List:")

        await self.controller.start()

        try:
            status = self.controller.get_system_status()
            sync_status = status.get('sync_engine', {})

            print(f"\nActive Tasks: {sync_status.get('active_tasks', 0)}")
            print(f"Completed Tasks: {sync_status.get('completed_tasks', 0)}")
            print(f"Failed Tasks: {sync_status.get('failed_tasks', 0)}")
            print(f"Queue Size: {sync_status.get('queue_size', 0)}")

            stats = sync_status.get('statistics', {})
            if stats:
                print(f"\nStatistics:")
                print(f"  Total Records Synced: {stats.get('total_synced', 0)}")
                print(f"  Total Failures: {stats.get('total_failed', 0)}")
                print(f"  Sync Speed: {stats.get('sync_speed', 0):.2f} records/sec")

                if stats.get('last_error'):
                    print(f"  Last Error: {stats['last_error']}")

        finally:
            await self.controller.stop()

    async def _cmd_daemon(self, args):
        """Run the controller in daemon mode"""
        print("🚀 Starting TradingView Data Sync & Backup daemon...")

        # Enable scheduled tasks for daemon mode
        daemon_config = self.config.copy()
        daemon_config['schedule_enabled'] = True

        controller = DataSyncBackupController(daemon_config)

        try:
            await controller.start()
            print("✅ Daemon started")
            print("   Press Ctrl+C to stop service")

            # Keep running
            while True:
                await asyncio.sleep(60)

                # Output status every minute in verbose mode
                if args.verbose:
                    status = controller.get_system_status()
                    sync_stats = status.get('sync_engine', {})
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Active tasks: {sync_stats.get('active_tasks', 0)}, "
                          f"Queue: {sync_stats.get('queue_size', 0)}")

        except KeyboardInterrupt:
            print("\n📴 Stopping daemon...")

        finally:
            await controller.stop()
            print("✅ Daemon stopped")

    async def _cmd_test(self, args):
        """Test system functionality"""
        print("🧪 Starting system functionality test...")

        await self.controller.start()

        try:
            # Test 1: System Status
            print("\n1️⃣ Testing system status...")
            status = self.controller.get_system_status()
            if status:
                print("   ✅ System status OK")
            else:
                print("   ❌ System status error")

            # Test 2: Create Test Backup
            print("\n2️⃣ Testing backup creation...")
            backup_id = await self.controller.create_manual_backup(
                BackupType.SNAPSHOT,
                symbols=['BINANCE:BTCUSDT'],
                timeframes=['15']
            )

            if backup_id:
                print(f"   ✅ Backup created successfully: {backup_id}")

                # Test 3: Restore Backup
                print("\n3️⃣ Testing backup restore...")
                success = await self.controller.restore_from_backup(backup_id)
                if success:
                    print("   ✅ Backup restore successful")
                else:
                    print("   ❌ Backup restore failed")
            else:
                print("   ❌ Backup creation failed")

            # Test 4: Data Sync
            print("\n4️⃣ Testing data synchronization...")
            task_id = await self.controller.sync_data(
                "primary", "cache",
                ['BINANCE:BTCUSDT'], ['15']
            )

            if task_id:
                print(f"   ✅ Sync task created successfully: {task_id}")

                # Wait for task completion
                await asyncio.sleep(3)

                final_status = self.controller.get_system_status()
                sync_stats = final_status.get('sync_engine', {}).get('statistics', {})

                if sync_stats.get('total_synced', 0) > 0:
                    print("   ✅ Data sync successful")
                else:
                    print("   ⚠️  Sync task still in progress")
            else:
                print("   ❌ Sync task creation failed")

            print("\n🎉 System functionality test complete!")

        finally:
            await self.controller.stop()


def create_parser():
    """Create command-line parser"""
    parser = argparse.ArgumentParser(
        description='TradingView Data Sync and Backup CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example Usage:
  # Check system status
  python sync_backup_cli.py status

  # Create full backup
  python sync_backup_cli.py backup --type full

  # Create incremental backup for specific symbols
  python sync_backup_cli.py backup --type incremental --symbols BINANCE:BTCUSDT,BINANCE:ETHUSDT

  # Restore backup
  python sync_backup_cli.py restore backup_full_1699123456

  # Sync data
  python sync_backup_cli.py sync --source primary --target cache --symbols BINANCE:BTCUSDT

  # List all backups
  python sync_backup_cli.py list backups

  # Start daemon
  python sync_backup_cli.py daemon

  # Run system tests
  python sync_backup_cli.py test
        """
    )

    parser.add_argument(
        '-c', '--config',
        help='Config file path',
        default='tradingview/sync_backup_config.yaml'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # status command
    subparsers.add_parser('status', help='View system status')

    # backup command
    backup_parser = subparsers.add_parser('backup', help='Create backup')
    backup_parser.add_argument(
        '--type',
        choices=['full', 'incremental', 'snapshot'],
        required=True,
        help='Backup type'
    )
    backup_parser.add_argument(
        '--symbols',
        help='Symbols to backup (comma-separated)'
    )
    backup_parser.add_argument(
        '--timeframes',
        help='Timeframes to backup (comma-separated)'
    )

    # restore command
    restore_parser = subparsers.add_parser('restore', help='Restore backup')
    restore_parser.add_argument(
        'backup_id',
        help='Backup ID'
    )
    restore_parser.add_argument(
        '--target-db',
        help='Target database file path'
    )
    restore_parser.add_argument(
        '--force',
        action='store_true',
        help='Force restore without confirmation'
    )

    # sync command
    sync_parser = subparsers.add_parser('sync', help='Execute data synchronization')
    sync_parser.add_argument(
        '--source',
        choices=['primary', 'cache', 'backup'],
        required=True,
        help='Source data type'
    )
    sync_parser.add_argument(
        '--target',
        choices=['cache', 'backup', 'remote'],
        required=True,
        help='Target data type'
    )
    sync_parser.add_argument(
        '--symbols',
        help='Symbols to sync (comma-separated)'
    )
    sync_parser.add_argument(
        '--timeframes',
        help='Timeframes to sync (comma-separated)'
    )
    sync_parser.add_argument(
        '--wait',
        action='store_true',
        help='Wait for sync task completion'
    )

    # list command
    list_parser = subparsers.add_parser('list', help='List backups or tasks')
    list_parser.add_argument(
        'type',
        choices=['backups', 'tasks'],
        help='List type'
    )
    list_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Detailed information'
    )

    # daemon command
    daemon_parser = subparsers.add_parser('daemon', help='Run in daemon mode')
    daemon_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    # test command
    subparsers.add_parser('test', help='Run system functionality tests')

    return parser


async def main():
    """Main function"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Set log level
    if args.verbose:
        logger.setLevel('DEBUG')

    # Create CLI instance and run command
    cli = SyncBackupCLI(args.config)
    await cli.run_command(args)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(0)
