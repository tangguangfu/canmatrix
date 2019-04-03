#!/usr/bin/env python

# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

#
# this script axports arxml-files from a canmatrix-object
# arxml-files are the can-matrix-definitions and a lot more in AUTOSAR-Context
# currently Support for Autosar 3.2 and 4.0-4.3 is planned

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import decimal
import logging
import typing
from builtins import *

from lxml import etree

import canmatrix
import canmatrix.utils

logger = logging.getLogger(__name__)
default_float_factory = decimal.Decimal

clusterExporter = 1
clusterImporter = 1


def create_sub_element(parent, element_name, text=None):
    # type: (etree._Element, str, str) -> etree._Element
    sn = etree.SubElement(parent, element_name)
    if text is not None:
        sn.text = str(text)
    return sn


def get_base_type_of_signal(signal):
    # type: (canmatrix.Signal) -> typing.Tuple[str, int]
    if signal.is_float:
        if signal.size > 32:
            create_type = "double"
            size = 64
        else:
            create_type = "single"
            size = 32
    else:
        if signal.size > 32:
            if signal.is_signed:
                create_type = "sint64"
            else:
                create_type = "uint64"
            size = 64                            
        elif signal.size > 16:
            if signal.is_signed:
                create_type = "sint32"
            else:
                create_type = "uint32"
            size = 32                            
        elif signal.size > 8:
            if signal.is_signed:
                create_type = "sint16"
            else:
                create_type = "uint16"
            size = 16
        else:
            if signal.is_signed:
                create_type = "sint8"
            else:
                create_type = "uint8"
            size = 8
    return create_type, size


def dump(dbs, f, **options):
    # type: (canmatrix.cancluster.CanCluster, typing.BinaryIO, **str) -> None
    ar_version = options.get("arVersion", "3.2.3")

    for name in dbs:
        db = dbs[name]  # type: canmatrix.CanMatrix
        for frame in db.frames:
            for signal in frame.signals:
                for rec in signal.receivers:
                    frame.add_receiver(rec.strip())

    if ar_version[0] == "3":
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element(
            'AUTOSAR',
            nsmap={
                None: 'http://autosar.org/' + ar_version,
                'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://autosar.org/' + ar_version + ' AUTOSAR_' + ar_version.replace('.', '') + '.xsd'
        top_level_packages = create_sub_element(root, 'TOP-LEVEL-PACKAGES')
    else:
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        root = etree.Element(
            'AUTOSAR',
            nsmap={
                None: "http://autosar.org/schema/r4.0",
                'xsi': xsi})
        root.attrib['{{{pre}}}schemaLocation'.format(
            pre=xsi)] = 'http://autosar.org/schema/r4.0 AUTOSAR_' + ar_version.replace('.', '-') + '.xsd'
        top_level_packages = create_sub_element(root, 'AR-PACKAGES')

    #
    # AR-PACKAGE Cluster
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Cluster')
    elements = create_sub_element(ar_package, 'ELEMENTS')

    for name in dbs:
        db = dbs[name]
        # if len(name) == 0:
        #    (path, ext) = os.path.splitext(filename)
        #    bus_name = path
        # else:
        if len(name) > 0:
            bus_name = name
        else:
            bus_name = "CAN"

        can_cluster = create_sub_element(elements, 'CAN-CLUSTER')
        create_sub_element(can_cluster, 'SHORT-NAME', bus_name)
        if ar_version[0] == "3":
            # createSubElement(can_cluster, 'SPEED', '50000')
            physical_channels = create_sub_element(can_cluster, 'PHYSICAL-CHANNELS')
            physical_channel = create_sub_element(physical_channels, 'PHYSICAL-CHANNEL')
            create_sub_element(physical_channel, 'SHORT-NAME', 'CAN')
            frame_triggering = create_sub_element(physical_channel, 'FRAME-TRIGGERINGSS')
        else:
            can_cluster_variants = create_sub_element(can_cluster, 'CAN-CLUSTER-VARIANTS')
            can_cluster_conditional = create_sub_element(can_cluster_variants, 'CAN-CLUSTER-CONDITIONAL')
            physical_channels = create_sub_element(can_cluster_conditional, 'PHYSICAL-CHANNELS')
            physical_channel = create_sub_element(physical_channels, 'CAN-PHYSICAL-CHANNEL')
            create_sub_element(physical_channel, 'SHORT-NAME', 'CAN')
            frame_triggering = create_sub_element(physical_channel, 'FRAME-TRIGGERINGS')
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                logger.error("Export complex multiplexers is not supported - ignoring frame %s", frame.name)
                continue
            can_frame_triggering = create_sub_element(frame_triggering, 'CAN-FRAME-TRIGGERING')
            create_sub_element(can_frame_triggering, 'SHORT-NAME', frame.name)
            frame_port_refs = create_sub_element(can_frame_triggering, 'FRAME-PORT-REFS')
            for transmitter in frame.transmitters:
                frame_port_ref = create_sub_element(frame_port_refs, 'FRAME-PORT-REF')
                frame_port_ref.set('DEST', 'FRAME-PORT')
                frame_port_ref.text = "/ECU/{0}/CN_{0}/{1}".format(transmitter, frame.name)
            for rec in frame.receivers:
                frame_port_ref = create_sub_element(frame_port_refs, 'FRAME-PORT-REF')
                frame_port_ref.set('DEST', 'FRAME-PORT')
                frame_port_ref.text = "/ECU/{0}/CN_{0}/{1}".format(rec, frame.name)
            frame_ref = create_sub_element(can_frame_triggering, 'FRAME-REF')
            if ar_version[0] == "3":
                frame_ref.set('DEST', 'FRAME')
                frame_ref.text = "/Frame/FRAME_{0}".format(frame.name)
                pdu_triggering_refs = create_sub_element(can_frame_triggering, 'I-PDU-TRIGGERING-REFS')
                pdu_triggering_ref = create_sub_element(pdu_triggering_refs, 'I-PDU-TRIGGERING-REF')
                pdu_triggering_ref.set('DEST', 'I-PDU-TRIGGERING')
            else:
                frame_ref.set('DEST', 'CAN-FRAME')
                frame_ref.text = "/CanFrame/FRAME_{0}".format(frame.name)
                pdu_triggering = create_sub_element(can_frame_triggering, 'PDU-TRIGGERINGS')
                pdu_triggering_ref_conditional = create_sub_element(pdu_triggering, 'PDU-TRIGGERING-REF-CONDITIONAL')
                pdu_triggering_ref = create_sub_element(pdu_triggering_ref_conditional, 'PDU-TRIGGERING-REF')
                pdu_triggering_ref.set('DEST', 'PDU-TRIGGERING')

            if frame.arbitration_id.extended is False:
                create_sub_element(can_frame_triggering, 'CAN-ADDRESSING-MODE', 'STANDARD')
            else:
                create_sub_element(can_frame_triggering, 'CAN-ADDRESSING-MODE', 'EXTENDED')
            create_sub_element(can_frame_triggering, 'IDENTIFIER', str(frame.arbitration_id.id))

            pdu_triggering_ref.text = "/Cluster/CAN/IPDUTRIGG_{0}".format(frame.name)

        if ar_version[0] == "3":
            ipdu_triggerings = create_sub_element(physical_channel, 'I-PDU-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                ipdu_triggering = create_sub_element(ipdu_triggerings, 'I-PDU-TRIGGERING')
                create_sub_element(ipdu_triggering, 'SHORT-NAME', "IPDUTRIGG_{0}".format(frame.name))
                ipdu_ref = create_sub_element(ipdu_triggering, 'I-PDU-REF')
                ipdu_ref.set('DEST', 'SIGNAL-I-PDU')
                ipdu_ref.text = "/PDU/PDU_{0}".format(frame.name)
            isignal_triggerings = create_sub_element(physical_channel, 'I-SIGNAL-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue
                for signal in frame.signals:
                    isignal_triggering = create_sub_element(isignal_triggerings, 'I-SIGNAL-TRIGGERING')
                    create_sub_element(isignal_triggering, 'SHORT-NAME', signal.name)
                    isignal_port_refs = create_sub_element(isignal_triggering, 'I-SIGNAL-PORT-REFS')

                    for receiver in signal.receivers:
                        isignal_port_ref = create_sub_element(
                            isignal_port_refs,
                            'I-SIGNAL-PORT-REF',
                            '/ECU/{0}/CN_{0}/{1}'.format(receiver, signal.name))
                        isignal_port_ref.set('DEST', 'SIGNAL-PORT')

                    isignal_ref = create_sub_element(
                        isignal_triggering, 'SIGNAL-REF')
                    isignal_ref.set('DEST', 'I-SIGNAL')
                    isignal_ref.text = "/ISignal/{}".format(signal.name)
        else:
            isignal_triggerings = create_sub_element(physical_channel, 'I-SIGNAL-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    isignal_triggering = create_sub_element(isignal_triggerings, 'I-SIGNAL-TRIGGERING')
                    create_sub_element(isignal_triggering, 'SHORT-NAME', signal.name)
                    isignal_port_refs = create_sub_element(isignal_triggering, 'I-SIGNAL-PORT-REFS')
                    for receiver in signal.receivers:
                        isignal_port_ref = create_sub_element(
                            isignal_port_refs,
                            'I-SIGNAL-PORT-REF',
                            '/ECU/{0}/CN_{0}/{1}'.format(receiver, signal.name))
                        isignal_port_ref.set('DEST', 'I-SIGNAL-PORT')

                    isignal_ref = create_sub_element(isignal_triggering, 'I-SIGNAL-REF')
                    isignal_ref.set('DEST', 'I-SIGNAL')
                    isignal_ref.text = "/ISignal/{0}".format(signal.name)
            ipdu_triggerings = create_sub_element(physical_channel, 'PDU-TRIGGERINGS')
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                ipdu_triggering = create_sub_element(ipdu_triggerings, 'PDU-TRIGGERING')
                create_sub_element(
                    ipdu_triggering,
                    'SHORT-NAME',
                    "IPDUTRIGG_{0}".format(frame.name))
                # missing: I-PDU-PORT-REFS
                ipdu_ref = create_sub_element(ipdu_triggering, 'I-PDU-REF')
                ipdu_ref.set('DEST', 'I-SIGNAL-I-PDU')
                ipdu_ref.text = "/PDU/PDU_{0}".format(frame.name)
                # missing: I-SIGNAL-TRIGGERINGS

# TODO
#        ipdu_triggerings = createSubElement(physical_channel, 'PDU-TRIGGERINGS')
#        for frame in db.frames:
#            ipdu_triggering = createSubElement(ipdu_triggerings, 'PDU-TRIGGERING')
#            createSubElement(ipdu_triggering, 'SHORT-NAME', "PDUTRIGG_{0}".format(frame.name))
#            ipdu_ref = createSubElement(ipdu_triggering, 'I-PDU-REF')
#            ipdu_ref.set('DEST','SIGNAL-I-PDU')
#            ipdu_ref.text = "/PDU/PDU_{0}".format(frame.name)

    #
    # AR-PACKAGE FRAME
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    if ar_version[0] == "3":
        create_sub_element(ar_package, 'SHORT-NAME', 'Frame')
    else:
        create_sub_element(ar_package, 'SHORT-NAME', 'CanFrame')

    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        # TODO: reused frames will be paced multiple times in file
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            if ar_version[0] == "3":
                frame_ele = create_sub_element(elements, 'FRAME')
            else:
                frame_ele = create_sub_element(elements, 'CAN-FRAME')
            create_sub_element(frame_ele, 'SHORT-NAME', "FRAME_{0}".format(frame.name))
            if frame.comment:
                desc = create_sub_element(frame_ele, 'DESC')
                l2 = create_sub_element(desc, 'L-2')
                l2.set("L", "FOR-ALL")
                l2.text = frame.comment
            create_sub_element(frame_ele, 'FRAME-LENGTH', "%d" % frame.size)
            pdu_mappings = create_sub_element(frame_ele, 'PDU-TO-FRAME-MAPPINGS')
            pdu_mapping = create_sub_element(pdu_mappings, 'PDU-TO-FRAME-MAPPING')
            create_sub_element(pdu_mapping, 'SHORT-NAME', frame.name)
            create_sub_element(pdu_mapping, 'PACKING-BYTE-ORDER', "MOST-SIGNIFICANT-BYTE-LAST")
            pdu_ref = create_sub_element(pdu_mapping, 'PDU-REF')
            create_sub_element(pdu_mapping, 'START-POSITION', '0')
            pdu_ref.text = "/PDU/PDU_{0}".format(frame.name)
            if ar_version[0] == "3":
                pdu_ref.set('DEST', 'SIGNAL-I-PDU')
            else:
                pdu_ref.set('DEST', 'I-SIGNAL-I-PDU')

    #
    # AR-PACKAGE PDU
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'PDU')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            if ar_version[0] == "3":
                signal_ipdu = create_sub_element(elements, 'SIGNAL-I-PDU')
                create_sub_element(signal_ipdu, 'SHORT-NAME', "PDU_{}".format(frame.name))
                create_sub_element(signal_ipdu, 'LENGTH', str(frame.size * 8))
            else:
                signal_ipdu = create_sub_element(elements, 'I-SIGNAL-I-PDU')
                create_sub_element(signal_ipdu, 'SHORT-NAME', "PDU_{}".format(frame.name))
                create_sub_element(signal_ipdu, 'LENGTH', str(frame.size))

            # I-PDU-TIMING-SPECIFICATION
            if ar_version[0] == "3":
                signal_to_pdu_mappings = create_sub_element(signal_ipdu, 'SIGNAL-TO-PDU-MAPPINGS')
            else:
                signal_to_pdu_mappings = create_sub_element(signal_ipdu, 'I-SIGNAL-TO-PDU-MAPPINGS')

            for signal in frame.signals:
                signal_to_pdu_mapping = create_sub_element(signal_to_pdu_mappings, 'I-SIGNAL-TO-I-PDU-MAPPING')
                create_sub_element(signal_to_pdu_mapping, 'SHORT-NAME', signal.name)

                if ar_version[0] == "3":
                    if signal.is_little_endian:  # Intel
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-LAST')
                    else:  # Motorola
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-FIRST')
                    signal_ref = create_sub_element(signal_to_pdu_mapping, 'SIGNAL-REF')
                else:
                    signal_ref = create_sub_element(signal_to_pdu_mapping, 'I-SIGNAL-REF')
                    if signal.is_little_endian:  # Intel
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-LAST')
                    else:  # Motorola
                        create_sub_element(
                            signal_to_pdu_mapping,
                            'PACKING-BYTE-ORDER',
                            'MOST-SIGNIFICANT-BYTE-FIRST')
                signal_ref.text = "/ISignal/{0}".format(signal.name)
                signal_ref.set('DEST', 'I-SIGNAL')

                create_sub_element(signal_to_pdu_mapping, 'START-POSITION',
                                   str(signal.get_startbit(bit_numbering=1)))
                # missing: TRANSFER-PROPERTY: PENDING/...

            for group in frame.signalGroups:
                signal_to_pdu_mapping = create_sub_element(signal_to_pdu_mappings, 'I-SIGNAL-TO-I-PDU-MAPPING')
                create_sub_element(signal_to_pdu_mapping, 'SHORT-NAME', group.name)
                signal_ref = create_sub_element(signal_to_pdu_mapping, 'SIGNAL-REF')
                signal_ref.text = "/ISignal/{}".format(group.name)
                signal_ref.set('DEST', 'I-SIGNAL')
                # TODO: TRANSFER-PROPERTY: PENDING???

    #
    # AR-PACKAGE ISignal
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'ISignal')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                signal_ele = create_sub_element(elements, 'I-SIGNAL')
                create_sub_element(signal_ele, 'SHORT-NAME', signal.name)
                if ar_version[0] == "4":
                    create_sub_element(signal_ele, 'LENGTH', str(signal.size))

                    network_represent_props = create_sub_element(
                        signal_ele, 'NETWORK-REPRESENTATION-PROPS')
                    sw_data_def_props_variants = create_sub_element(
                        network_represent_props, 'SW-DATA-DEF-PROPS-VARIANTS')
                    sw_data_def_props_conditional = create_sub_element(
                        sw_data_def_props_variants, 'SW-DATA-DEF-PROPS-CONDITIONAL')
                    
                    base_type_ref = create_sub_element(sw_data_def_props_conditional, 'BASE-TYPE-REF')
                    base_type_ref.set('DEST', 'SW-BASE-TYPE')
                    create_type, size = get_base_type_of_signal(signal)
                    base_type_ref.text = "/DataType/{}".format(create_type)
                    compu_method_ref = create_sub_element(
                        sw_data_def_props_conditional,
                        'COMPU-METHOD-REF',
                        '/DataType/Semantics/{}'.format(signal.name))
                    compu_method_ref.set('DEST', 'COMPU-METHOD')
                    unit_ref = create_sub_element(
                        sw_data_def_props_conditional,
                        'UNIT-REF',
                        '/DataType/Unit/{}'.format(signal.name))
                    unit_ref.set('DEST', 'UNIT')

                sys_sig_ref = create_sub_element(signal_ele, 'SYSTEM-SIGNAL-REF')
                sys_sig_ref.text = "/Signal/{}".format(signal.name)

                sys_sig_ref.set('DEST', 'SYSTEM-SIGNAL')
            for group in frame.signalGroups:
                signal_ele = create_sub_element(elements, 'I-SIGNAL')
                create_sub_element(signal_ele, 'SHORT-NAME', group.name)
                sys_sig_ref = create_sub_element(signal_ele, 'SYSTEM-SIGNAL-REF')
                sys_sig_ref.text = "/Signal/{}".format(group.name)
                sys_sig_ref.set('DEST', 'SYSTEM-SIGNAL-GROUP')

    #
    # AR-PACKAGE Signal
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Signal')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                signal_ele = create_sub_element(elements, 'SYSTEM-SIGNAL')
                create_sub_element(signal_ele, 'SHORT-NAME', signal.name)
                if signal.comment:
                    desc = create_sub_element(signal_ele, 'DESC')
                    l2 = create_sub_element(desc, 'L-2')
                    l2.set("L", "FOR-ALL")
                    l2.text = signal.comment
                if ar_version[0] == "3":
                    data_type_ref = create_sub_element(signal_ele, 'DATA-TYPE-REF')
                    if signal.is_float:
                        data_type_ref.set('DEST', 'REAL-TYPE')
                    else:
                        data_type_ref.set('DEST', 'INTEGER-TYPE')
                    data_type_ref.text = "/DataType/{}".format(signal.name)
                    create_sub_element(signal_ele, 'LENGTH', str(signal.size))
                # init_value_ref = create_sub_element(signal_ele, 'INIT-VALUE-REF')
                # init_value_ref.set('DEST', 'INTEGER-LITERAL')
                # init_value_ref.text = "/CONSTANTS/{}".format(signal.name)
            for group in frame.signalGroups:
                group_ele = create_sub_element(elements, 'SYSTEM-SIGNAL-GROUP')
                create_sub_element(group_ele, 'SHORT-NAME', group.name)
                if ar_version[0] == "3":
                    data_type_ref.set('DEST', 'INTEGER-TYPE')  # todo check this
                sys_signal_refs = create_sub_element(
                    group_ele, 'SYSTEM-SIGNAL-REFS')
                for member in group.signals:
                    member_ele = create_sub_element(
                        sys_signal_refs, 'SYSTEM-SIGNAL-REF')
                    member_ele.set('DEST', 'SYSTEM-SIGNAL')
                    member_ele.text = "/Signal/{}".format(member.name)

    #
    # AR-PACKAGE Datatype
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'DataType')
    elements = create_sub_element(ar_package, 'ELEMENTS')

    if ar_version[0] == "3":
        for name in dbs:
            db = dbs[name]
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    if signal.is_float:
                        type_ele = create_sub_element(elements, 'REAL-TYPE')
                    else:
                        type_ele = create_sub_element(elements, 'INTEGER-TYPE')
                    create_sub_element(type_ele, 'SHORT-NAME', signal.name)
                    sw_data_def_props = create_sub_element(
                        type_ele, 'SW-DATA-DEF-PROPS')
                    if signal.is_float:
                        encoding = create_sub_element(type_ele, 'ENCODING')
                        if signal.size > 32:
                            encoding.text = "DOUBLE"
                        else:
                            encoding.text = "SINGLE"
                    compu_method_ref = create_sub_element(sw_data_def_props, 'COMPU-METHOD-REF')
                    compu_method_ref.set('DEST', 'COMPU-METHOD')
                    compu_method_ref.text = "/DataType/Semantics/{}".format(signal.name)
    else:
        created_types = []  # type: typing.List[str]
        for name in dbs:
            db = dbs[name]
            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                for signal in frame.signals:
                    create_type, size = get_base_type_of_signal(signal)
                    if create_type not in created_types:
                        created_types.append(create_type)
                        sw_base_type = create_sub_element(elements, 'SW-BASE-TYPE')
                        create_sub_element(sw_base_type, 'SHORT-NAME', create_type)
                        create_sub_element(sw_base_type, 'CATEGORY', 'FIXED_LENGTH')
                        create_sub_element(sw_base_type, 'BASE-TYPE-SIZE', str(size))
                        if signal.is_float:
                            create_sub_element(sw_base_type, 'BASE-TYPE-ENCODING', 'IEEE754')

    if ar_version[0] == "3":
        subpackages = create_sub_element(ar_package, 'SUB-PACKAGES')
    else:
        subpackages = create_sub_element(ar_package, 'AR-PACKAGES')
    ar_package = create_sub_element(subpackages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Semantics')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                compu_method = create_sub_element(elements, 'COMPU-METHOD')
                create_sub_element(compu_method, 'SHORT-NAME', signal.name)
                # missing: UNIT-REF
                compu_int_to_phys = create_sub_element(
                    compu_method, 'COMPU-INTERNAL-TO-PHYS')
                compu_scales = create_sub_element(compu_int_to_phys, 'COMPU-SCALES')
                for value in sorted(signal.values, key=lambda x: int(x)):
                    compu_scale = create_sub_element(compu_scales, 'COMPU-SCALE')
                    desc = create_sub_element(compu_scale, 'DESC')
                    l2 = create_sub_element(desc, 'L-2')
                    l2.set('L', 'FOR-ALL')
                    l2.text = signal.values[value]
                    create_sub_element(compu_scale, 'LOWER-LIMIT', str(value))
                    create_sub_element(compu_scale, 'UPPER-LIMIT', str(value))
                    compu_const = create_sub_element(compu_scale, 'COMPU-CONST')
                    create_sub_element(compu_const, 'VT', signal.values[value])
                else:
                    compu_scale = create_sub_element(compu_scales, 'COMPU-SCALE')
                    # createSubElement(compuScale, 'LOWER-LIMIT', str(#TODO))
                    # createSubElement(compuScale, 'UPPER-LIMIT', str(#TODO))
                    compu_rationsl_coeff = create_sub_element(compu_scale, 'COMPU-RATIONAL-COEFFS')
                    compu_numerator = create_sub_element(compu_rationsl_coeff, 'COMPU-NUMERATOR')
                    create_sub_element(compu_numerator, 'V', "%g" % signal.offset)
                    create_sub_element(compu_numerator, 'V', "%g" % signal.factor)
                    compu_denomiator = create_sub_element(compu_rationsl_coeff, 'COMPU-DENOMINATOR')
                    create_sub_element(compu_denomiator, 'V', "1")

    ar_package = create_sub_element(subpackages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'Unit')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                continue

            for signal in frame.signals:
                unit = create_sub_element(elements, 'UNIT')
                create_sub_element(unit, 'SHORT-NAME', signal.name)
                create_sub_element(unit, 'DISPLAY-NAME', signal.unit)

    tx_ipdu_groups = {}  # type: typing.Dict[str, typing.List[str]]
    rx_ipdu_groups = {}  # type: typing.Dict[str, typing.List[str]]

    #
    # AR-PACKAGE ECU
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'ECU')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for name in dbs:
        db = dbs[name]
        for ecu in db.ecus:
            ecu_instance = create_sub_element(elements, 'ECU-INSTANCE')
            create_sub_element(ecu_instance, 'SHORT-NAME', ecu.name)
            if ecu.comment:
                desc = create_sub_element(ecu_instance, 'DESC')
                l2 = create_sub_element(desc, 'L-2')
                l2.set('L', 'FOR-ALL')
                l2.text = ecu.comment

            if ar_version[0] == "3":
                asso_ipdu_group_refs = create_sub_element(
                    ecu_instance, 'ASSOCIATED-I-PDU-GROUP-REFS')
                connectors = create_sub_element(ecu_instance, 'CONNECTORS')
                comm_connector = create_sub_element(connectors, 'COMMUNICATION-CONNECTOR')
            else:
                asso_ipdu_group_refs = create_sub_element(ecu_instance, 'ASSOCIATED-COM-I-PDU-GROUP-REFS')
                connectors = create_sub_element(ecu_instance, 'CONNECTORS')
                comm_connector = create_sub_element(connectors, 'CAN-COMMUNICATION-CONNECTOR')

            create_sub_element(comm_connector, 'SHORT-NAME', 'CN_' + ecu.name)
            ecu_comm_port_instances = create_sub_element(comm_connector, 'ECU-COMM-PORT-INSTANCES')

            rec_temp = None
            send_temp = None

            for frame in db.frames:
                if frame.is_complex_multiplexed:
                    continue

                if ecu.name in frame.transmitters:
                    frame_port = create_sub_element(ecu_comm_port_instances, 'FRAME-PORT')
                    create_sub_element(frame_port, 'SHORT-NAME', frame.name)
                    create_sub_element(frame_port, 'COMMUNICATION-DIRECTION', 'OUT')
                    send_temp = 1
                    if ecu.name + "_Tx" not in tx_ipdu_groups:
                        tx_ipdu_groups[ecu.name + "_Tx"] = []
                    tx_ipdu_groups[ecu.name + "_Tx"].append(frame.name)

                    # missing I-PDU-PORT
                    for signal in frame.signals:
                        if ar_version[0] == "3":
                            signal_port = create_sub_element(ecu_comm_port_instances, 'SIGNAL-PORT')
                        else:
                            signal_port = create_sub_element(ecu_comm_port_instances, 'I-SIGNAL-PORT')

                        create_sub_element(signal_port, 'SHORT-NAME', signal.name)
                        create_sub_element(signal_port, 'COMMUNICATION-DIRECTION', 'OUT')
                if ecu.name in frame.receivers:
                    frame_port = create_sub_element(ecu_comm_port_instances, 'FRAME-PORT')
                    create_sub_element(frame_port, 'SHORT-NAME', frame.name)
                    create_sub_element(frame_port, 'COMMUNICATION-DIRECTION', 'IN')
                    rec_temp = 1
                    if ecu.name + "_Tx" not in rx_ipdu_groups:
                        rx_ipdu_groups[ecu.name + "_Rx"] = []
                    rx_ipdu_groups[ecu.name + "_Rx"].append(frame.name)

                    # missing I-PDU-PORT
                    for signal in frame.signals:
                        if ecu.name in signal.receivers:
                            if ar_version[0] == "3":
                                signal_port = create_sub_element(ecu_comm_port_instances, 'SIGNAL-PORT')
                            else:
                                signal_port = create_sub_element(ecu_comm_port_instances, 'I-SIGNAL-PORT')

                            create_sub_element(signal_port, 'SHORT-NAME', signal.name)
                            create_sub_element(signal_port, 'COMMUNICATION-DIRECTION', 'IN')

            if rec_temp is not None:
                if ar_version[0] == "3":
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-PDU-GROUP")
                else:
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-COM-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-SIGNAL-I-PDU-GROUP")

                asso_ipdu_group_ref.text = "/IPDUGroup/{0}_Rx".format(ecu.name)

            if send_temp is not None:
                if ar_version[0] == "3":
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-PDU-GROUP")
                else:
                    asso_ipdu_group_ref = create_sub_element(asso_ipdu_group_refs, 'ASSOCIATED-COM-I-PDU-GROUP-REF')
                    asso_ipdu_group_ref.set('DEST', "I-SIGNAL-I-PDU-GROUP")
                asso_ipdu_group_ref.text = "/IPDUGroup/{}_Tx".format(ecu.name)

    #
    # AR-PACKAGE IPDUGroup
    #
    ar_package = create_sub_element(top_level_packages, 'AR-PACKAGE')
    create_sub_element(ar_package, 'SHORT-NAME', 'IPDUGroup')
    elements = create_sub_element(ar_package, 'ELEMENTS')
    for pdu_group in tx_ipdu_groups:
        if ar_version[0] == "3":
            ipdu_grp = create_sub_element(elements, 'I-PDU-GROUP')
        else:
            ipdu_grp = create_sub_element(elements, 'I-SIGNAL-I-PDU-GROUP')

        create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
        create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "OUT")

        if ar_version[0] == "3":
            ipdu_refs = create_sub_element(ipdu_grp, 'I-PDU-REFS')
            for frame_name in tx_ipdu_groups[pdu_group]:
                ipdu_ref = create_sub_element(ipdu_refs, 'I-PDU-REF')
                ipdu_ref.set('DEST', "SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_{}".format(frame_name)
        else:
            isignal_ipdus = create_sub_element(ipdu_grp, 'I-SIGNAL-I-PDUS')
            for frame_name in tx_ipdu_groups[pdu_group]:
                isignal_ipdu_ref_conditional = create_sub_element(isignal_ipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipdu_ref = create_sub_element(isignal_ipdu_ref_conditional, 'I-SIGNAL-I-PDU-REF')
                ipdu_ref.set('DEST', "I-SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_{}".format(frame_name)

    if ar_version[0] == "3":
        for pdu_group in rx_ipdu_groups:
            ipdu_grp = create_sub_element(elements, 'I-PDU-GROUP')
            create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
            create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "IN")

            ipdu_refs = create_sub_element(ipdu_grp, 'I-PDU-REFS')
            for frame_name in rx_ipdu_groups[pdu_group]:
                ipdu_ref = create_sub_element(ipdu_refs, 'I-PDU-REF')
                ipdu_ref.set('DEST', "SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_{}".format(frame_name)
    else:
        for pdu_group in rx_ipdu_groups:
            ipdu_grp = create_sub_element(elements, 'I-SIGNAL-I-PDU-GROUP')
            create_sub_element(ipdu_grp, 'SHORT-NAME', pdu_group)
            create_sub_element(ipdu_grp, 'COMMUNICATION-DIRECTION', "IN")
            isignal_ipdus = create_sub_element(ipdu_grp, 'I-SIGNAL-I-PDUS')
            for frame_name in rx_ipdu_groups[pdu_group]:
                isignal_ipdu_ref_conditional = create_sub_element(isignal_ipdus, 'I-SIGNAL-I-PDU-REF-CONDITIONAL')
                ipdu_ref = create_sub_element(isignal_ipdu_ref_conditional, 'I-SIGNAL-I-PDU-REF')
                ipdu_ref.set('DEST', "I-SIGNAL-I-PDU")
                ipdu_ref.text = "/PDU/PDU_" + frame_name

    f.write(etree.tostring(root, pretty_print=True, xml_declaration=True))

###################################
# read ARXML
###################################


class arTree(object):
    def __init__(self, name="", ref=None):
        self._name = name
        self._ref = ref
        self._array = []  # type: typing.List[arTree]
    def new(self, name, child):
        temp = arTree(name, child)
        self._array.append(temp)
        return temp
    def getChild(self, path):
        for tem in self._array:
            if tem._name == path:
                return tem


def arParseTree(tag, ardict, namespace):
    # type: (etree._Element, arTree, str) -> None
    for child in tag:
        name = child.find('./' + namespace + 'SHORT-NAME')
#               namel = child.find('./' + namespace + 'LONG-NAME')
        if name is not None and child is not None:
            arParseTree(child, ardict.new(name.text, child), namespace)
        if name is None and child is not None:
            arParseTree(child, ardict, namespace)


def arGetXchildren(root, path, arDict, ns):
    # type: (etree._Element, str, arTree, str) -> typing.Sequence[etree._Element]
    pathElements = path.split('/')
    ptr = root
    for element in pathElements[:-1]:
        ptr = arGetChild(ptr, element, arDict, ns)
    ptr = arGetChildren(ptr, pathElements[-1], arDict, ns)
    return ptr

#
# get path in tranlation-dictionary
#


def arPath2xPath(arPath, destElement=None):
    # type: (str, typing.Optional[str]) -> str
    arPathElements = arPath.strip('/').split('/')
    xpath = "."

    for element in arPathElements[:-1]:
        xpath += "//A:SHORT-NAME[text()='" + element + "']/.."
    if destElement:
        xpath += "//A:" + destElement + "/A:SHORT-NAME[text()='" + arPathElements[-1] + "']/.."
    else:
        xpath += "//A:SHORT-NAME[text()='" + arPathElements[-1] + "']/.."

    return xpath


ArCache = dict()  # type: typing.Dict[str, etree._Element]


def getArPath(tree, arPath, namespaces):
    global ArCache
    namespaceMap = {'A': namespaces[1:-1]}
    baseARPath = arPath[:arPath.rfind('/')]
    if baseARPath in ArCache:
        baseElement = ArCache[baseARPath]
    else:
        xbasePath= arPath2xPath(baseARPath)
        baseElement = tree.xpath(xbasePath, namespaces=namespaceMap)[0]
        ArCache[baseARPath] = baseElement
    found = baseElement.xpath(".//A:SHORT-NAME[text()='" + arPath[arPath.rfind('/')+1:] + "']/..", namespaces=namespaceMap)[0]
    return found


def arGetPath(ardict, path):
    # type: (arTree, str) -> typing.Optional[etree._Element]
    ptr = ardict
    for p in path.split('/'):
        if p.strip():
            if ptr is not None:
                try:
                    ptr = ptr.getChild(p)
                except:
                    return None
            else:
                return None
    if ptr is not None:
        return ptr._ref
    else:
        return None


def arGetChild(parent, tagname, xmlRoot, namespace):
    # type: (etree._Element, str, etree._Element, str) -> typing.Optional[etree._Element]
    # logger.debug("getChild: " + tagname)
    if parent is None:
        return None
    ret = parent.find('.//' + namespace + tagname)
    if ret is None:
        ret = parent.find('.//' + namespace + tagname + '-REF')
        if ret is not None:
            if isinstance(xmlRoot, arTree):
                ret = arGetPath(xmlRoot, ret.text)
            else:
                ret = getArPath(xmlRoot, ret.text, namespace)
    return ret


def arGetChildren(parent, tagname, arTranslationTable, namespace):
    if parent is None:
        return []
    ret = parent.findall('.//' + namespace + tagname)
    if ret.__len__() == 0:
        retlist = parent.findall('.//' + namespace + tagname + '-REF')
        rettemp = []
        for ret in retlist:
            rettemp.append(arGetPath(arTranslationTable, ret.text))
        ret = rettemp
    return ret


def arGetName(parent, ns):
    # type: (etree._Element, str) -> str
    name = parent.find('./' + ns + 'SHORT-NAME')
    if name is not None:
        if name.text is not None:
            return name.text
    return ""


pduFrameMapping = {}
signalRxs = {}


def getSysSignals(syssignal, syssignalarray, frame, Id, ns):
    members = []
    for signal in syssignalarray:
        members.append(arGetName(signal, ns))
    frame.add_signal_group(arGetName(syssignal, ns), 1, members)


def decodeCompuMethod(compuMethod, arDict, ns, float_factory):
    values = {}
    factor = float_factory(1.0)
    offset = float_factory(0)
    unit = arGetChild(compuMethod, "UNIT", arDict, ns)
    const = None
    compuscales = arGetXchildren(compuMethod, "COMPU-INTERNAL-TO-PHYS/COMPU-SCALES/COMPU-SCALE", arDict, ns)
    for compuscale in compuscales:
        ll = arGetChild(compuscale, "LOWER-LIMIT", arDict, ns)
        ul = arGetChild(compuscale, "UPPER-LIMIT", arDict, ns)
        sl = arGetChild(compuscale, "SHORT-LABEL", arDict, ns)
        if sl is None:
            desc = get_desc(compuscale, arDict, ns)
        else:
            desc = sl.text
        #####################################################################################################
        # Modification to support sourcing the COMPU_METHOD info from the Vector NETWORK-REPRESENTATION-PROPS
        # keyword definition. 06Jun16
        #####################################################################################################
        if ll is not None and desc is not None and int(float_factory(ul.text)) == int(float_factory(ll.text)):
            #####################################################################################################
            #####################################################################################################
            values[ll.text] = desc

        scaleDesc = get_desc(compuscale, arDict, ns)
        rational = arGetChild(compuscale, "COMPU-RATIONAL-COEFFS", arDict, ns)
        if rational is not None:
            numerator = arGetChild(rational, "COMPU-NUMERATOR", arDict, ns)
            zaehler = arGetChildren(numerator, "V", arDict, ns)
            denominator = arGetChild(rational, "COMPU-DENOMINATOR", arDict, ns)
            nenner = arGetChildren(denominator, "V", arDict, ns)

            factor = float_factory(zaehler[1].text) / float_factory(nenner[0].text)
            offset = float_factory(zaehler[0].text) / float_factory(nenner[0].text)
        else:
            const = arGetChild(compuscale, "COMPU-CONST", arDict, ns)
            # value hinzufuegen
            if const is None:
                logger.warn(
                    "unknown Compu-Method: at sourceline %d " % compuMethod.sourceline)
    return values, factor, offset, unit, const

def get_signals(signalarray, frame, xmlRoot, ns, multiplex_id, float_factory):
    global signalRxs
    GroupId = 1
    if signalarray is None:  # Empty signalarray - nothing to do
        return
    for signal in signalarray:
        compmethod = None
        motorolla = arGetChild(signal, "PACKING-BYTE-ORDER", xmlRoot, ns)
        startBit = arGetChild(signal, "START-POSITION", xmlRoot, ns)

        isignal = arGetChild(signal, "SIGNAL", xmlRoot, ns)
        if isignal is None:
            isignal = arGetChild(signal, "I-SIGNAL", xmlRoot, ns)
        if isignal is None:
            isignal = arGetChild(signal, "I-SIGNAL-GROUP", xmlRoot, ns)
            if isignal is not None:
                logger.debug("get_signals: found I-SIGNAL-GROUP ")

                isignalarray = arGetXchildren(isignal, "I-SIGNAL", xmlRoot, ns)
                getSysSignals(isignal, isignalarray, frame, GroupId, ns)
                GroupId = GroupId + 1
                continue
        if isignal is None:
            logger.debug(
                'Frame %s, no isignal for %s found',
                frame.name,arGetChild(signal, "SHORT-NAME", xmlRoot, ns).text)

        baseType = arGetChild(isignal,"BASE-TYPE", xmlRoot, ns)
        sig_long_name = arGetChild(isignal, "LONG-NAME", xmlRoot, ns)
        if sig_long_name is not None:
            sig_long_name = arGetChild(sig_long_name, "L-4", xmlRoot, ns)
            if sig_long_name is not None:
                sig_long_name = sig_long_name.text
        syssignal = arGetChild(isignal, "SYSTEM-SIGNAL", xmlRoot, ns)
        if syssignal is None:
            logger.debug('Frame %s, signal %s has no systemsignal', isignal.tag, frame.name)

        if "SYSTEM-SIGNAL-GROUP" in syssignal.tag:
            syssignalarray = arGetXchildren(syssignal, "SYSTEM-SIGNAL-REFS/SYSTEM-SIGNAL", xmlRoot, ns)
            getSysSignals(syssignal, syssignalarray, frame, GroupId, ns)
            GroupId = GroupId + 1
            continue

        length = arGetChild(isignal, "LENGTH", xmlRoot, ns)
        if length is None:
            length = arGetChild(syssignal, "LENGTH", xmlRoot, ns)

        name = arGetChild(syssignal, "SHORT-NAME", xmlRoot, ns)
        unitElement = arGetChild(isignal, "UNIT", xmlRoot, ns)
        displayName = arGetChild(unitElement, "DISPLAY-NAME", xmlRoot, ns)
        if displayName is not None:
            Unit = displayName.text
        else:
            Unit = ""

        Min = None
        Max = None
        receiver = []  # type: typing.List[str]

        signalDescription = get_desc(syssignal, xmlRoot, ns)

        datatype = arGetChild(syssignal, "DATA-TYPE", xmlRoot, ns)
        if datatype is None:  # AR4?
            dataConstr = arGetChild(isignal,"DATA-CONSTR", xmlRoot, ns)
            compmethod = arGetChild(isignal,"COMPU-METHOD", xmlRoot, ns)
            baseType  = arGetChild(isignal,"BASE-TYPE", xmlRoot, ns)
            lower = arGetChild(dataConstr, "LOWER-LIMIT", xmlRoot, ns)
            upper = arGetChild(dataConstr, "UPPER-LIMIT", xmlRoot, ns)
            encoding = None # TODO - find encoding in AR4
        else:
            lower = arGetChild(datatype, "LOWER-LIMIT", xmlRoot, ns)
            upper = arGetChild(datatype, "UPPER-LIMIT", xmlRoot, ns)
            encoding = arGetChild(datatype, "ENCODING", xmlRoot, ns)

        if encoding is not None and (encoding.text == "SINGLE" or encoding.text == "DOUBLE"):
            is_float = True
        else:
            is_float = False
        
        if lower is not None and upper is not None:
            Min = float_factory(lower.text)
            Max = float_factory(upper.text)

        datdefprops = arGetChild(datatype, "SW-DATA-DEF-PROPS", xmlRoot, ns)

        if compmethod is None:
            compmethod = arGetChild(datdefprops, "COMPU-METHOD", xmlRoot, ns)
        if compmethod is None:  # AR4
            compmethod = arGetChild(isignal, "COMPU-METHOD", xmlRoot, ns)
            baseType = arGetChild(isignal, "BASE-TYPE", xmlRoot, ns)
            encoding = arGetChild(baseType, "BASE-TYPE-ENCODING", xmlRoot, ns)
            if encoding is not None and encoding.text == "IEEE754":
                is_float = True
        if compmethod == None:
            logger.debug('No Compmethod found!! - try alternate scheme 1.')
            networkrep = arGetChild(isignal, "NETWORK-REPRESENTATION-PROPS", xmlRoot, ns)
            datdefpropsvar = arGetChild(networkrep, "SW-DATA-DEF-PROPS-VARIANTS", xmlRoot, ns)
            datdefpropscond = arGetChild(datdefpropsvar, "SW-DATA-DEF-PROPS-CONDITIONAL", xmlRoot ,ns)
            if datdefpropscond != None:
                try:
                    compmethod = arGetChild(datdefpropscond, "COMPU-METHOD", xmlRoot, ns)
                except:
                    logger.debug('No valid compu method found for this - check ARXML file!!')
                    compmethod = None
        #####################################################################################################
        # no found compu-method fuzzy search in systemsignal:
        #####################################################################################################
        if compmethod == None:
            logger.debug('No Compmethod found!! - fuzzy search in syssignal.')
            compmethod = arGetChild(syssignal, "COMPU-METHOD", xmlRoot, ns)

        # decode compuMethod:
        (values, factor, offset, unit, const) = decodeCompuMethod(compmethod, xmlRoot, ns, float_factory)

        if Min is not None:
            Min *= factor
            Min += offset
        if Max is not None:
            Max *= factor
            Max += offset

        if baseType is None:
            baseType = arGetChild(datdefprops, "BASE-TYPE", xmlRoot, ns)
        if baseType is not None:
            typeName = arGetName(baseType, ns)
            if typeName[0] == 'u':
                is_signed = False  # unsigned
            else:
                is_signed = True  # signed
        else:
            is_signed = True  # signed

        if unit is not None:
            longname = arGetChild(unit, "LONG-NAME", xmlRoot, ns)
        #####################################################################################################
        # Modification to support obtaining the Signals Unit by DISPLAY-NAME. 07June16
        #####################################################################################################
            try:
              displayname = arGetChild(unit, "DISPLAY-NAME", xmlRoot, ns)
            except:
              logger.debug('No Unit Display name found!! - using long name')
            if displayname is not None:
              Unit = displayname.text
            else:
              l4 = arGetChild(longname, "L-4", xmlRoot, ns)
              if l4 is not None:
                Unit = l4.text

        init_list = arGetXchildren(syssignal, "INIT-VALUE/VALUE", xmlRoot, ns)

        if not init_list:
            init_list = arGetXchildren(isignal, "INIT-VALUE/NUMERICAL-VALUE-SPECIFICATION/VALUE", xmlRoot, ns)  # #AR4.2
        if init_list:
            initvalue = init_list[0]
        else:
            initvalue = None

        is_little_endian = False
        if motorolla is not None:
            if motorolla.text == 'MOST-SIGNIFICANT-BYTE-LAST':
                is_little_endian = True
        else:
            logger.debug('no name byte order for signal' + name.text)

        if name is None:
            logger.debug('no name for signal given')
        if startBit is None:
            logger.debug('no startBit for signal given')
        if length is None:
            logger.debug('no length for signal given')

        if startBit is not None:
            newSig = canmatrix.Signal(name.text,
                                      start_bit=int(startBit.text),
                                      size=int(length.text),
                                      is_little_endian=is_little_endian,
                                      is_signed=is_signed,
                                      factor=factor,
                                      offset=offset,
                                      unit=Unit,
                                      receivers=receiver,
                                      multiplex=multiplex_id,
                                      comment=signalDescription,
                                      is_float=is_float)

            if Min is not None:
                newSig.min = Min
            if Max is not None:
                newSig.max = Max

            if newSig.is_little_endian == 0:
                # startbit of motorola coded signals are MSB in arxml
                newSig.set_startbit(int(startBit.text), bitNumbering=1)

            # save signal, to determin receiver-ECUs for this signal later
            signalRxs[syssignal] = newSig

            if baseType is not None:
                temp = arGetChild(baseType, "SHORT-NAME", xmlRoot, ns)
                if temp is not None and "boolean" == temp.text:
                    newSig.add_values(1, "TRUE")
                    newSig.add_values(0, "FALSE")


            if initvalue is not None and initvalue.text is not None:
                initvalue.text = canmatrix.utils.guess_value(initvalue.text)
                newSig._initValue = int(initvalue.text)
                newSig.add_attribute("GenSigStartValue", str(newSig._initValue))
            else:
                newSig._initValue = 0

            for key, value in list(values.items()):
                newSig.add_values(key, value)
            if sig_long_name is not None:
                newSig.add_attribute("LongName", sig_long_name)
            frame.add_signal(newSig)


def get_frame(frameTriggering, xmlRoot, multiplexTranslation, ns, float_factory):
    global pduFrameMapping
    extEle = arGetChild(frameTriggering, "CAN-ADDRESSING-MODE", xmlRoot, ns)
    idele = arGetChild(frameTriggering, "IDENTIFIER", xmlRoot, ns)
    frameR = arGetChild(frameTriggering, "FRAME", xmlRoot, ns)

    sn = arGetChild(frameTriggering, "SHORT-NAME", xmlRoot, ns)
    logger.debug("processing Frame: %s", sn.text)
    if idele is None:
        logger.info("found Frame %s without arbitration id %s", sn.text)
        return None
    arbitration_id = int(idele.text)

    if frameR is not None:
        dlc = arGetChild(frameR, "FRAME-LENGTH", xmlRoot, ns)
        pdumappings = arGetChild(frameR, "PDU-TO-FRAME-MAPPINGS", xmlRoot, ns)
        pdumapping = arGetChild(pdumappings, "PDU-TO-FRAME-MAPPING", xmlRoot, ns)
        pdu = arGetChild(pdumapping, "PDU", xmlRoot, ns)  # SIGNAL-I-PDU

        if pdu is not None and 'SECURED-I-PDU' in pdu.tag:
            logger.info("found secured pdu - no signal extraction possible: %s", arGetName(pdu,ns))

        pduFrameMapping[pdu] = arGetName(frameR, ns)

        new_frame = canmatrix.Frame(arGetName(frameR, ns), size=int(dlc.text))
        comment = get_desc(frameR, xmlRoot, ns)
        if comment is not None:
            new_frame.add_comment(comment)
    else:
        # without frameinfo take short-name of frametriggering and dlc = 8
        logger.debug("Frame %s has no FRAME-REF" % (sn))
        ipduTriggeringRefs = arGetChild(frameTriggering, "I-PDU-TRIGGERING-REFS", xmlRoot, ns)
        ipduTriggering = arGetChild(ipduTriggeringRefs, "I-PDU-TRIGGERING", xmlRoot, ns)
        pdu = arGetChild(ipduTriggering, "I-PDU", xmlRoot, ns)
        if pdu is None:
            pdu = arGetChild(ipduTriggering, "I-SIGNAL-I-PDU", xmlRoot, ns) ## AR4.2
        dlc = arGetChild(pdu, "LENGTH", xmlRoot, ns)
        new_frame = canmatrix.Frame(sn.text, arbitration_id=arbitration_id, size=int(int(dlc.text) / 8))

    if pdu is None:
        logger.error("ERROR: pdu")
    else:
        logger.debug(arGetName(pdu, ns))

    if pdu is not None and "MULTIPLEXED-I-PDU" in pdu.tag:
        selectorByteOrder = arGetChild(pdu, "SELECTOR-FIELD-BYTE-ORDER", xmlRoot, ns)
        selectorLen = arGetChild(pdu, "SELECTOR-FIELD-LENGTH", xmlRoot, ns)
        selectorStart = arGetChild(pdu, "SELECTOR-FIELD-START-POSITION", xmlRoot, ns)
        is_little_endian = False
        if selectorByteOrder.text == 'MOST-SIGNIFICANT-BYTE-LAST':
            is_little_endian = True
        is_signed = False  # unsigned
        multiplexor = canmatrix.Signal("Multiplexor",start_bit=int(selectorStart.text),size=int(selectorLen.text),
                             is_little_endian=is_little_endian,multiplex="Multiplexor")

        multiplexor._initValue = 0
        new_frame.add_signal(multiplexor)
        staticPart = arGetChild(pdu, "STATIC-PART", xmlRoot, ns)
        ipdu = arGetChild(staticPart, "I-PDU", xmlRoot, ns)
        if ipdu is not None:
            pdusigmappings = arGetChild(ipdu, "SIGNAL-TO-PDU-MAPPINGS", xmlRoot, ns)
            pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", xmlRoot, ns)
            get_signals(pdusigmapping, new_frame, xmlRoot, ns, None, float_factory)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu, ns)

        dynamicPart = arGetChild(pdu, "DYNAMIC-PART", xmlRoot, ns)
#               segmentPositions = arGetChild(dynamicPart, "SEGMENT-POSITIONS", arDict, ns)
#               segmentPosition = arGetChild(segmentPositions, "SEGMENT-POSITION", arDict, ns)
#               byteOrder = arGetChild(segmentPosition, "SEGMENT-BYTE-ORDER", arDict, ns)
#               segLength = arGetChild(segmentPosition, "SEGMENT-LENGTH", arDict, ns)
#               segPos = arGetChild(segmentPosition, "SEGMENT-POSITION", arDict, ns)
        dynamicPartAlternatives = arGetChild(dynamicPart, "DYNAMIC-PART-ALTERNATIVES", xmlRoot, ns)
        dynamicPartAlternativeList = arGetChildren(dynamicPartAlternatives, "DYNAMIC-PART-ALTERNATIVE", xmlRoot, ns)
        for alternative in dynamicPartAlternativeList:
            selectorId = arGetChild(alternative, "SELECTOR-FIELD-CODE", xmlRoot, ns)
            ipdu = arGetChild(alternative, "I-PDU", xmlRoot, ns)
            multiplexTranslation[arGetName(ipdu, ns)] = arGetName(pdu, ns)
            if ipdu is not None:
                pdusigmappings = arGetChild(ipdu, "SIGNAL-TO-PDU-MAPPINGS", xmlRoot, ns)
                pdusigmapping = arGetChildren(pdusigmappings, "I-SIGNAL-TO-I-PDU-MAPPING", xmlRoot, ns)
                get_signals(pdusigmapping, new_frame, xmlRoot, ns, selectorId.text, float_factory)

    if new_frame.comment is None:
        new_frame.add_comment(get_desc(pdu, xmlRoot, ns))

    if extEle is not None and  extEle.text == 'EXTENDED':
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended = True)
    else:
        new_frame.arbitration_id = canmatrix.ArbitrationId(arbitration_id, extended=False)

    timingSpec = arGetChild(pdu, "I-PDU-TIMING-SPECIFICATION", xmlRoot, ns)
    if timingSpec is None:
        timingSpec = arGetChild(pdu, "I-PDU-TIMING-SPECIFICATIONS", xmlRoot, ns)
    cyclicTiming = arGetChild(timingSpec, "CYCLIC-TIMING", xmlRoot, ns)
    repeatingTime = arGetChild(cyclicTiming, "REPEATING-TIME", xmlRoot, ns)

    eventTiming = arGetChild(timingSpec, "EVENT-CONTROLLED-TIMING", xmlRoot, ns)
    repeats = arGetChild(eventTiming, "NUMBER-OF-REPEATS", xmlRoot, ns)
    minimumDelay = arGetChild(timingSpec, "MINIMUM-DELAY", xmlRoot, ns)
    startingTime = arGetChild(timingSpec, "STARTING-TIME", xmlRoot, ns)

    timeOffset = arGetChild(cyclicTiming, "TIME-OFFSET", xmlRoot, ns)
    timePeriod = arGetChild(cyclicTiming, "TIME-PERIOD", xmlRoot, ns)

    if cyclicTiming is not None and eventTiming is not None:
        new_frame.add_attribute("GenMsgSendType", "cyclicAndSpontanX")        # CycleAndSpontan
        if minimumDelay is not None:
            new_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimumDelay.text) * 1000)))
        if repeats is not None:
            new_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    elif cyclicTiming is not None:
        new_frame.add_attribute("GenMsgSendType", "cyclicX")  # CycleX
        if minimumDelay is not None:
            new_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimumDelay.text) * 1000)))
        if repeats is not None:
            new_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)
    else:
        new_frame.add_attribute("GenMsgSendType", "spontanX")  # Spontan
        if minimumDelay is not None:
            new_frame.add_attribute("GenMsgDelayTime", str(int(float_factory(minimumDelay.text) * 1000)))
        if repeats is not None:
            new_frame.add_attribute("GenMsgNrOfRepetitions", repeats.text)

    if startingTime is not None:
        value = arGetChild(startingTime, "VALUE", xmlRoot, ns)
        new_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))
    elif cyclicTiming is not None:
        value = arGetChild(timeOffset, "VALUE", xmlRoot, ns)
        if value is not None:
            new_frame.add_attribute("GenMsgStartDelayTime", str(int(float_factory(value.text) * 1000)))

    value = arGetChild(repeatingTime, "VALUE", xmlRoot, ns)
    if value is not None:
        new_frame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))
    elif cyclicTiming is not None:
        value = arGetChild(timePeriod, "VALUE", xmlRoot, ns)
        if value is not None:
            new_frame.add_attribute("GenMsgCycleTime", str(int(float_factory(value.text) * 1000)))


#    pdusigmappings = arGetChild(pdu, "SIGNAL-TO-PDU-MAPPINGS", arDict, ns)
#    if pdusigmappings is None or pdusigmappings.__len__() == 0:
#        logger.debug("DEBUG: Frame %s no SIGNAL-TO-PDU-MAPPINGS found" % (new_frame.name))
    pdusigmapping = arGetChildren(pdu, "I-SIGNAL-TO-I-PDU-MAPPING", xmlRoot, ns)

    if pdusigmapping is not None and pdusigmapping.__len__() > 0:
        get_signals(pdusigmapping, new_frame, xmlRoot, ns, None, float_factory)

    # Seen some pdusigmapping being [] and not None with some arxml 4.2
    else: ##AR 4.2
        pdutrigs = arGetChildren(frameTriggering, "PDU-TRIGGERINGS", xmlRoot, ns)
        if pdutrigs is not None:
            for pdutrig in pdutrigs:
                trigrefcond = arGetChild(pdutrig, "PDU-TRIGGERING-REF-CONDITIONAL", xmlRoot, ns)
                trigs = arGetChild(trigrefcond, "PDU-TRIGGERING", xmlRoot, ns)
                ipdus = arGetChild(trigs, "I-PDU", xmlRoot, ns)

                signaltopdumaps = arGetChild(ipdus, "I-SIGNAL-TO-PDU-MAPPINGS", xmlRoot, ns)
                if signaltopdumaps is None:
                    signaltopdumaps = arGetChild(ipdus, "I-SIGNAL-TO-I-PDU-MAPPINGS", xmlRoot, ns)

                if signaltopdumaps is None:
                    logger.debug("DEBUG: AR4.x PDU %s no SIGNAL-TO-PDU-MAPPINGS found - no signal extraction!" % (arGetName(ipdus, ns)))
#                signaltopdumap = arGetChild(signaltopdumaps, "I-SIGNAL-TO-I-PDU-MAPPING", arDict, ns)
                get_signals(signaltopdumaps, new_frame, xmlRoot, ns, None, float_factory)
        else:
            logger.debug("DEBUG: Frame %s (assuming AR4.2) no PDU-TRIGGERINGS found" % (new_frame.name))
    return new_frame


def get_desc(element, arDict, ns):
    desc = arGetChild(element, "DESC", arDict, ns)
    txt = arGetChild(desc, 'L-2[@L="DE"]', arDict, ns)
    if txt is None:
        txt = arGetChild(desc, 'L-2[@L="EN"]', arDict, ns)
    if txt is None:
        txt = arGetChild(desc, 'L-2', arDict, ns)
    if txt is not None:
        return txt.text
    else:
        return ""

def process_ecu(ecu, db, arDict, multiplexTranslation, ns):
    global pduFrameMapping
    connectors = arGetChild(ecu, "CONNECTORS", arDict, ns)
    diagAddress = arGetChild(ecu, "DIAGNOSTIC-ADDRESS", arDict, ns)
    diagResponse = arGetChild(ecu, "RESPONSE-ADDRESSS", arDict, ns)
    # TODO: use diagAddress for frame-classification
    commconnector = arGetChild(connectors,"COMMUNICATION-CONNECTOR",arDict,ns)
    if commconnector is None:
        commconnector = arGetChild(connectors, "CAN-COMMUNICATION-CONNECTOR", arDict, ns)
    frames = arGetXchildren(commconnector,"ECU-COMM-PORT-INSTANCES/FRAME-PORT",arDict,ns)
    nmAddress = arGetChild(commconnector, "NM-ADDRESS", arDict, ns)
    assocRefs = arGetChild(ecu, "ASSOCIATED-I-PDU-GROUP-REFS", arDict, ns)

    if assocRefs is not None:
        assoc = arGetChildren(assocRefs, "ASSOCIATED-I-PDU-GROUP", arDict, ns)
    else:  # AR4
        assocRefs = arGetChild(ecu, "ASSOCIATED-COM-I-PDU-GROUP-REFS", arDict, ns)
        assoc = arGetChildren(assocRefs,"ASSOCIATED-COM-I-PDU-GROUP",arDict,ns)

    inFrame = []
    outFrame = []

    # get direction of frames (is current ECU sender/receiver/...?)
    for ref in assoc:
        direction = arGetChild(ref, "COMMUNICATION-DIRECTION", arDict, ns)
        groupRefs = arGetChild(ref, "CONTAINED-I-PDU-GROUPS-REFS", arDict, ns)
        pdurefs = arGetChild(ref, "I-PDU-REFS", arDict, ns)
        if pdurefs is not None:  # AR3
           # local defined pdus
            pdus = arGetChildren(pdurefs, "I-PDU", arDict, ns)
            for pdu in pdus:
                if pdu in pduFrameMapping:
                    if direction.text == "IN":
                        inFrame.append(pduFrameMapping[pdu])
                    else:
                        outFrame.append(pduFrameMapping[pdu])
        else:  # AR4
            isigpdus = arGetChild(ref, "I-SIGNAL-I-PDUS", arDict, ns)
            isigconds = arGetChildren(
                isigpdus, "I-SIGNAL-I-PDU-REF-CONDITIONAL", arDict, ns)
            for isigcond in isigconds:
                pdus = arGetChildren(isigcond, "I-SIGNAL-I-PDU", arDict, ns)
                for pdu in pdus:
                    if pdu in pduFrameMapping:
                        if direction.text == "IN":
                            inFrame.append(pduFrameMapping[pdu])
                        else:
                            outFrame.append(pduFrameMapping[pdu])

        # grouped pdus
        group = arGetChildren(groupRefs, "CONTAINED-I-PDU-GROUPS", arDict, ns)
        for t in group:
            if direction is None:
                direction = arGetChild(
                    t, "COMMUNICATION-DIRECTION", arDict, ns)
            pdurefs = arGetChild(t, "I-PDU-REFS", arDict, ns)
            pdus = arGetChildren(pdurefs, "I-PDU", arDict, ns)
            for pdu in pdus:
                if direction.text == "IN":
                    inFrame.append(arGetName(pdu, ns))
                else:
                    outFrame.append(arGetName(pdu, ns))

        for out in outFrame:
            if out in multiplexTranslation:
                out = multiplexTranslation[out]
            frame = db.frame_by_name(out)
            if frame is not None:
                frame.add_transmitter(arGetName(ecu, ns))
            else:
                pass

#               for inf in inFrame:
#                       if inf in multiplexTranslation:
#                               inf = multiplexTranslation[inf]
#                       frame = db.frameByName(inf)
#                       if frame is not None:
#                               for signal in frame.signals:
#                                       recname = arGetName(ecu, ns)
#                                       if recname not in  signal.receiver:
#                                               signal.receiver.append(recname)
#                       else:
#                               print "in not found: " + inf
    bu = ecu(arGetName(ecu, ns))
    if nmAddress is not None:
        bu.add_attribute("NWM-Stationsadresse", nmAddress.text)
        bu.add_attribute("NWM-Knoten", "ja")
    else:
        bu.add_attribute("NWM-Stationsadresse", "0")
        bu.add_attribute("NWM-Knoten", "nein")
    return bu

def ecuc_extract_signal(signal_node, ns):
    attributes = signal_node.findall(".//" + ns + "DEFINITION-REF")
    start_bit = None
    size = 0
    endianness = None
    init_value = 0
    signal_type = None
    timeout = 0
    for attribute in attributes:
        if attribute.text.endswith("ComBitPosition"):
            start_bit = int(attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComBitSize"):
            size = int(attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComSignalEndianness"):
            endianness = (attribute.getparent().find(".//" +ns + "VALUE").text)
            if "LITTLE_ENDIAN" in endianness:
                is_little = True
            else:
                is_little = False
        if attribute.text.endswith("ComSignalInitValue"):
            init_value = int(attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComSignalType"):
            signal_type = (attribute.getparent().find(".//" +ns + "VALUE").text)
        if attribute.text.endswith("ComTimeout"):
            timeout = int(attribute.getparent().find(".//" +ns + "VALUE").text)
    return canmatrix.Signal(arGetName(signal_node,ns), start_bit = start_bit, size=size, is_little_endian = is_little)

def extract_cm_from_ecuc(com_module, search_point, ns):
    db = canmatrix.CanMatrix()
    definitions = com_module.findall('.//' + ns + "DEFINITION-REF")
    for definition in definitions:
        if definition.text.endswith("ComIPdu"):
            container = definition.getparent()
            frame = canmatrix.Frame(arGetName(container, ns))
            db.add_frame(frame)
            allReferences = arGetChildren(container,"ECUC-REFERENCE-VALUE",search_point,ns)
            for reference in allReferences:
                value = arGetChild(reference,"VALUE",search_point,ns)
                if value is not None:
                    signal_definition = value.find('./' + ns + "DEFINITION-REF")
                    if signal_definition.text.endswith("ComSignal"):
                        signal = ecuc_extract_signal(value,ns)
                        frame.add_signal(signal)
    db.recalc_dlc(strategy = "max")
    return {"": db}


def load(file, **options):
    # type: (typing.BinaryIO, **str) -> typing.Dict[str, canmatrix.CanMatrix]

    global ArCache
    ArCache = dict()
    global pduFrameMapping
    pduFrameMapping = {}
    global signalRxs
    signalRxs = {}

    float_factory = options.get("float_factory", default_float_factory)
    ignoreClusterInfo = options.get("arxmlIgnoreClusterInfo", False)
    useArXPath = options.get("arxmlUseXpath", False)

    result = {}
    logger.debug("Read arxml ...")
    tree = etree.parse(file)

    root = tree.getroot()
    logger.debug(" Done\n")

    ns = "{" + tree.xpath('namespace-uri(.)') + "}"
    nsp = tree.xpath('namespace-uri(.)')


    topLevelPackages = root.find('./' + ns + 'TOP-LEVEL-PACKAGES')

    if topLevelPackages is None:
        # no "TOP-LEVEL-PACKAGES found, try root
        topLevelPackages = root

    logger.debug("Build arTree ...")

    if useArXPath:
        searchPoint = topLevelPackages
    else:
        arDict = arTree()
        arParseTree(topLevelPackages, arDict, ns)
        searchPoint = arDict

    logger.debug(" Done\n")


    com_module = arGetPath(searchPoint, "ActiveEcuC/Com")
    if com_module is not None:
        logger.info("seems to be a ECUC arxml. Very limited support for extracting canmatrix." )
        return extract_cm_from_ecuc(com_module, searchPoint, ns)

    frames = root.findall('.//' + ns + 'CAN-FRAME')  ## AR4.2
    if frames is None:
        frames = root.findall('.//' + ns + 'FRAME') ## AR3.2-4.1?
    
    logger.debug("DEBUG %d frames in arxml..." % (frames.__len__()))
    canTriggers = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
    logger.debug(
        "DEBUG %d can-frame-triggering in arxml..." %
        (canTriggers.__len__()))

    sigpdumap = root.findall('.//' + ns + 'SIGNAL-TO-PDU-MAPPINGS')
    logger.debug(
        "DEBUG %d SIGNAL-TO-PDU-MAPPINGS in arxml..." %
        (sigpdumap.__len__()))

    sigIpdu = root.findall('.//' + ns + 'I-SIGNAL-TO-I-PDU-MAPPING')
    logger.debug(
        "DEBUG %d I-SIGNAL-TO-I-PDU-MAPPING in arxml..." %
        (sigIpdu.__len__()))

    if ignoreClusterInfo == True:
        ccs = {"ignoreClusterInfo"}
    else:
        ccs = root.findall('.//' + ns + 'CAN-CLUSTER')
    for cc in ccs:
        db = canmatrix.CanMatrix()
# Defines not jet imported...
        db.add_ecu_defines("NWM-Stationsadresse", 'HEX 0 63')
        db.add_ecu_defines("NWM-Knoten", 'ENUM  "nein","ja"')
        db.add_signal_defines("LongName", 'STRING')
        db.add_frame_defines("GenMsgCycleTime", 'INT 0 65535')
        db.add_frame_defines("GenMsgDelayTime", 'INT 0 65535')
        db.add_frame_defines("GenMsgNrOfRepetitions", 'INT 0 65535')
        db.add_frame_defines("GenMsgStartValue", 'STRING')
        db.add_frame_defines("GenMsgStartDelayTime", 'INT 0 65535')
        db.add_frame_defines(
            "GenMsgSendType",
            'ENUM  "cyclicX","spontanX","cyclicIfActiveX","spontanWithDelay","cyclicAndSpontanX","cyclicAndSpontanWithDelay","spontanWithRepitition","cyclicIfActiveAndSpontanWD","cyclicIfActiveFast","cyclicWithRepeatOnDemand","none"')
        db.add_signal_defines("GenSigStartValue", 'HEX 0 4294967295')

        if ignoreClusterInfo == True:
            canframetrig = root.findall('.//' + ns + 'CAN-FRAME-TRIGGERING')
            busname = ""
        else:
            speed = arGetChild(cc, "SPEED", searchPoint, ns)
            logger.debug("Busname: " + arGetName(cc, ns))

            busname = arGetName(cc, ns)
            if speed is not None:
                logger.debug(" Speed: " + speed.text)

            physicalChannels = cc.find('.//' + ns + "PHYSICAL-CHANNELS")
            if physicalChannels is None:
                logger.error("Error - PHYSICAL-CHANNELS not found")

            nmLowerId = arGetChild(cc, "NM-LOWER-CAN-ID", searchPoint, ns)

            physicalChannel = arGetChild(
                physicalChannels, "PHYSICAL-CHANNEL", searchPoint, ns)
            if physicalChannel is None:
                physicalChannel = arGetChild(
                    physicalChannels, "CAN-PHYSICAL-CHANNEL", searchPoint, ns)
            if physicalChannel is None:
                logger.debug("Error - PHYSICAL-CHANNEL not found")
            canframetrig = arGetChildren(
                physicalChannel, "CAN-FRAME-TRIGGERING", searchPoint, ns)
            if canframetrig is None:
                logger.error("Error - CAN-FRAME-TRIGGERING not found")
            else:
                logger.debug(
                    "%d frames found in arxml\n" %
                    (canframetrig.__len__()))

        multiplexTranslation = {}  # type: typing.Dict[str, str]
        for frameTrig in canframetrig:  # type: etree._Element
            frameObject = get_frame(frameTrig, searchPoint, multiplexTranslation, ns, float_factory)
            if frameObject is not None:
                db.add_frame(frameObject)
                
        if ignoreClusterInfo is True:
            pass
            # no support for signal direction
        else:
            isignaltriggerings = arGetXchildren(
                physicalChannel, "I-SIGNAL-TRIGGERING", searchPoint, ns)
            for sigTrig in isignaltriggerings:
                isignal = arGetChild(sigTrig, 'SIGNAL', searchPoint, ns)
                if isignal is None:
                    isignal = arGetChild(sigTrig, 'I-SIGNAL', searchPoint, ns)
                if isignal is None:
                    sigTrig_text = arGetName(sigTrig, ns) if sigTrig is not None else "None"
                    logger.debug("load: no isignal for %s" % sigTrig_text)
                    
                    continue

                portRef = arGetChildren(sigTrig, "I-SIGNAL-PORT", searchPoint, ns)

                for port in portRef:
                    comDir = arGetChild(
                        port, "COMMUNICATION-DIRECTION", searchPoint, ns)
                    if comDir is not None and comDir.text == "IN":
                        sysSignal = arGetChild(
                            isignal, "SYSTEM-SIGNAL", searchPoint, ns)
                        ecuName = arGetName(
                            port.getparent().getparent().getparent().getparent(), ns)
                        # port points in ECU; probably more stable to go up
                        # from each ECU than to go down in XML...
                        if sysSignal in signalRxs:
                            if ecuName not in signalRxs[sysSignal].receivers:
                                signalRxs[sysSignal].receivers.append(ecuName)
    # find ECUs:
        nodes = root.findall('.//' + ns + 'ECU-INSTANCE')
        for node in nodes:
            ecu = process_ecu(node, db, searchPoint, multiplexTranslation, ns)
            desc = arGetChild(node, "DESC", searchPoint, ns)
            l2 = arGetChild(desc, "L-2", searchPoint, ns)
            if l2 is not None:
                ecu.add_comment(l2.text)

            db.add_ecu(ecu)

        for frame in db.frames:
            sig_value_hash = dict()
            for sig in frame.signals:
                sig_value_hash[sig.name] = sig._initValue
            frameData = frame.encode(sig_value_hash)
            frame.add_attribute("GenMsgStartValue", "".join(["%02x" % x for x in frameData]))
        result[busname] = db
    return result
