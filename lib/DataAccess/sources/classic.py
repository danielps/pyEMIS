import logging, sys
from MySQLdb import connect, cursors, Error
from .. import config

class Classic(object):
    # doctest: +ELLIPSIS
    """
    The classic database uses a config object so it needs a config file.
    >>> import os.path, pyEMIS.DataAccess as DA
    >>> config_path = os.path.expanduser('~/.EMIS/config.cfg')
    >>> src = DA.sources.Classic(config_path, "Classic")
    >>> src #doctest: +ELLIPSIS
    <pyEMIS.DataAccess.sources.classic.Classic object at ...>
    >>>
    """
    def __init__(self, config_file, database='Classic'):
        self._logger = logging.getLogger('DataAccess:sources:Classic')
        conf = config(config_file, database)
        try:
            self.conn = connect(host=conf.host(), user=conf.user(), passwd=conf.password(), db=conf.db())
            self.cur = self.conn.cursor(cursors.DictCursor)
        except Error, e:
            if e.args[0] == 1045:
                self._logger.error('Invalid configuration for [%s] at %s' % (database, config_path))
                sys.exit(1)
            else:
                raise

    def _query(self, sql, *args):
        """
        The _query method is pretty straight forward.
        >>> import os.path, pyEMIS.DataAccess as DA, logging
        >>> config_path = os.path.expanduser('~/.EMIS/config.cfg')
        >>> src = DA.sources.DynamatPlus(config_path, "DynamatPlus")
        >>> src._query("SELECT Meter_ID, Description, meter_type FROM Meter WHERE Meter_ID = '%s'", 111)
        [{0: 111, 1: 'LEC/KIMB/EM01                 ', 2: 1, 'Description': 'LEC/KIMB/EM01                 ', 'meter_type': 1, 'Meter_ID': 111}]
        >>> 
        """
        try:
            if args:
                self._logger.debug(sql % (args))
                self.cur.execute(sql, (args))
            else:
                self._logger.debug(sql)
                self.cur.execute(sql)
            return self.cur.fetchall()
        except Error, e:
            if e.args[0] == 1054:
                self._logger.error("invalid sql")
                self._logger.error(e.args[1])
                self._logger.error(sql)
                sys.exit(1)
            else:
                raise

    def _old_query(self, sql):
        self._logger.debug(sql)
        try:
            self.cursor.execute (sql)
            return self.cursor.fetchall ()
        except Error, e:
            if e.args[0] == 1054:
                self._logger.error("invalid sql")
                self._logger.error(e.args[1])
                self._logger.error(sql)
                sys.exit(1)
            else:
                raise

    def movement(self, meter_id):
        sql = "SELECT DISTINCT date_sql as date, movement FROM tbl_meter_data WHERE channel_id = %s AND date_sql > 0 ORDER BY date_sql" % str(meter_id)
        return self._query(sql)

    def integ(self, meter_id):
        sql = "SELECT DISTINCT date_sql as datetime, integ as value FROM tbl_meter_data WHERE channel_id = %s AND date_sql > 0 ORDER BY date_sql" % str(meter_id)
        return self._query(sql)

    def meters(self):
        sql = """
        SELECT ch.id, ch.name, t.channel_type as type
        FROM tbl_channels AS ch
        LEFT JOIN tbl_channel_types as t ON ch.channel_type_id = t.id
        """
        return self._query(sql)

    def meter_with_units(self, meter_id):
        sql = """
        SELECT
        ch.id,
        ch.name,
        t.channel_type AS type,
        u.name AS unit,
        u.suffix,
        ch_u.multiplier,
        c.coefficient
        FROM
        tbl_channels AS ch
        Left Join tbl_channel_types AS t ON ch.channel_type_id = t.id
        Left Join tbl_channel_units AS ch_u ON ch.channel_unit_id = ch_u.id
        Left Join tbl_units AS u ON ch_u.unit_id = u.id
        Inner Join tbl_units AS base_units ON t.unit_id = base_units.id
        Inner Join tbl_unit_conversions as c ON u.id = c.from_unit_id AND base_units.id = c.to_unit_id
        WHERE ch.id = %s
        """ % str(int(meter_id))
        return self._query(sql)[0]

    def __del__(self):
        self.conn.close


if __name__ == "__main__":
    import doctest
    doctest.testmod()
